from __future__ import annotations

from dataclasses import replace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.db import Base
from app.core.user_context import CurrentUserContext
from app.models import AuditLogModel
from app.repositories import UserRepository
from app.services import AdminServiceError, AdminUserService, AuthService, AuthServiceError


def _build_session_local():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def _build_settings() -> Settings:
    return Settings(
        jwt_secret="phase2-jwt-secret",
        refresh_token_secret="phase2-refresh-secret",
        csrf_secret="phase2-csrf-secret",
        api_key_pepper="phase2-api-key-pepper",
        bootstrap_owner_email="owner@phase2.local",
        bootstrap_owner_display_name="Phase2 Owner",
        bootstrap_owner_api_key="cpk_test_phase2_bootstrap_owner_key_123456",
        access_token_ttl_seconds=300,
        refresh_token_ttl_seconds=3600,
        default_org_id="org_phase2",
    )


def _build_owner_context(repo: UserRepository, settings: Settings) -> CurrentUserContext:
    owner = repo.get_user_by_email(settings.bootstrap_owner_email)
    assert owner is not None
    membership = repo.get_first_active_membership(user_id=owner.id)
    assert membership is not None
    return CurrentUserContext(
        user_id=owner.id,
        org_id=membership.org_id,
        role=membership.role,
        email=owner.email,
        display_name=owner.display_name,
        status=owner.status,
        session_id=None,
    )


def test_admin_user_and_api_key_lifecycle_with_session_revoke() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()

    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        owner_ctx = _build_owner_context(repo, settings)
        admin_service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)

        created = admin_service.create_user(
            current_user=owner_ctx,
            email="member@phase2.local",
            display_name="Phase2 Member",
            role="MEMBER",
            org_id=None,
        )
        db.commit()
        assert created["email"] == "member@phase2.local"
        assert created["role"] == "MEMBER"

        users = admin_service.list_users(
            current_user=owner_ctx,
            query="member",
            role="MEMBER",
            user_status="ACTIVE",
            page=1,
            page_size=20,
        )
        assert users["total"] == 1
        member_id = users["items"][0]["id"]

        key = admin_service.issue_api_key(
            current_user=owner_ctx,
            user_id=member_id,
            name="member-laptop",
            expires_at=None,
        )
        db.commit()
        assert key.plain_text_key.startswith("cpk_live_")

        login = auth_service.login_with_api_key(
            api_key=key.plain_text_key,
            device_info="pytest-phase2",
            ip="127.0.0.1",
            user_agent="pytest",
        )
        db.commit()

        revoke_result = admin_service.revoke_api_key(current_user=owner_ctx, key_id=key.key_id)
        db.commit()
        assert revoke_result["success"] is True
        assert revoke_result["revokedSessions"] >= 1

        try:
            auth_service.refresh_access_token(
                refresh_token=login.refresh_token,
                csrf_header=login.csrf_token,
                csrf_cookie=login.csrf_token,
                ip="127.0.0.1",
                user_agent="pytest",
            )
        except AuthServiceError as exc:
            assert exc.error_code == "TOKEN_EXPIRED"
        else:
            raise AssertionError("Expected refresh failure after API key revoke")


def test_disable_user_revokes_all_sessions() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()

    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        owner_ctx = _build_owner_context(repo, settings)
        admin_service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)
        created = admin_service.create_user(
            current_user=owner_ctx,
            email="member2@phase2.local",
            display_name="Phase2 Member2",
            role="MEMBER",
            org_id=None,
        )
        db.commit()

        key = admin_service.issue_api_key(
            current_user=owner_ctx,
            user_id=created["id"],
            name="member2-laptop",
            expires_at=None,
        )
        db.commit()
        login = auth_service.login_with_api_key(
            api_key=key.plain_text_key,
            device_info="pytest-phase2-2",
            ip="127.0.0.1",
            user_agent="pytest",
        )
        db.commit()

        updated = admin_service.update_user_status(
            current_user=owner_ctx,
            user_id=created["id"],
            next_status="DISABLED",
        )
        db.commit()
        assert updated["status"] == "DISABLED"

        try:
            auth_service.get_current_user_from_access_token(login.access_token)
        except AuthServiceError as exc:
            assert exc.error_code in {"TOKEN_EXPIRED", "USER_DISABLED"}
        else:
            raise AssertionError("Expected disabled user session to be invalid")


def test_revoke_api_key_for_self_is_forbidden() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()

    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        owner_ctx = _build_owner_context(repo, settings)
        admin_service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)

        own_key = admin_service.issue_api_key(
            current_user=owner_ctx,
            user_id=owner_ctx.user_id,
            name="owner-self-key",
            expires_at=None,
        )
        db.commit()

        try:
            admin_service.revoke_api_key(current_user=owner_ctx, key_id=own_key.key_id)
        except AdminServiceError as exc:
            assert exc.error_code == "SELF_OPERATION_FORBIDDEN"
        else:
            raise AssertionError("Expected self revoke to be forbidden")


def test_create_user_rejects_cross_org_assignment() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()

    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        repo.get_or_create_organization(org_id="org_other", name="Other Org")
        db.commit()

        owner_ctx = _build_owner_context(repo, settings)
        admin_service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)

        try:
            admin_service.create_user(
                current_user=owner_ctx,
                email="cross-org@phase2.local",
                display_name="Cross Org",
                role="MEMBER",
                org_id="org_other",
            )
        except AdminServiceError as exc:
            assert exc.error_code == "PERMISSION_DENIED"
        else:
            raise AssertionError("Expected cross-org user creation to be rejected")


def test_create_user_requires_active_org_context() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()

    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        owner_ctx = _build_owner_context(repo, settings)
        no_org_ctx = replace(owner_ctx, org_id="")
        admin_service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)

        try:
            admin_service.create_user(
                current_user=no_org_ctx,
                email="no-org@phase2.local",
                display_name="No Org",
                role="MEMBER",
                org_id=None,
            )
        except AdminServiceError as exc:
            assert exc.error_code == "NO_ACTIVE_ORG"
        else:
            raise AssertionError("Expected NO_ACTIVE_ORG when current user has no org context")

        failed_audit = db.execute(
            select(AuditLogModel)
            .where(AuditLogModel.action == "ADMIN_CREATE_USER", AuditLogModel.result == "FAILED")
            .limit(1)
        ).scalar_one_or_none()
        assert failed_audit is not None
