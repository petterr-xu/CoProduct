from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.db import Base
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository
from app.services import AdminServiceError, AdminUserService, AuthService, AuthServiceError


def _build_session_local():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def _build_settings() -> Settings:
    return Settings(
        jwt_secret="phase4-jwt-secret",
        refresh_token_secret="phase4-refresh-secret",
        csrf_secret="phase4-csrf-secret",
        api_key_pepper="phase4-api-key-pepper",
        bootstrap_owner_email="owner@phase4.local",
        bootstrap_owner_display_name="Phase4 Owner",
        bootstrap_owner_api_key="cpk_test_phase4_bootstrap_owner_key_123456",
        access_token_ttl_seconds=300,
        refresh_token_ttl_seconds=3600,
        default_org_id="org_phase4",
    )


def _build_context(repo: UserRepository, email: str) -> CurrentUserContext:
    user = repo.get_user_by_email(email)
    assert user is not None
    membership = repo.get_first_active_membership(user_id=user.id)
    assert membership is not None
    return CurrentUserContext(
        user_id=user.id,
        org_id=membership.org_id,
        role=membership.role,
        email=user.email,
        display_name=user.display_name,
        status=user.status,
        session_id=None,
    )


def test_phase4_admin_cannot_operate_owner() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()
    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)
        owner_ctx = _build_context(repo, settings.bootstrap_owner_email)
        second_owner = service.create_user(
            current_user=owner_ctx,
            email="owner2@phase4.local",
            display_name="Owner 2",
            role="OWNER",
            org_id=None,
        )
        service.create_user(
            current_user=owner_ctx,
            email="admin@phase4.local",
            display_name="Admin A",
            role="ADMIN",
            org_id=None,
        )
        db.commit()

        admin_ctx = _build_context(repo, "admin@phase4.local")
        second_owner_membership = repo.get_membership(user_id=second_owner["id"], org_id=owner_ctx.org_id)
        assert second_owner_membership is not None

        with pytest.raises(AdminServiceError) as exc:
            service.update_member_status(
                current_user=admin_ctx,
                membership_id=second_owner_membership.id,
                member_status="SUSPENDED",
                reason="security incident",
            )
        assert exc.value.error_code == "OWNER_GUARD_VIOLATION"


def test_phase4_owner_self_demotion_is_forbidden() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()
    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)
        owner_ctx = _build_context(repo, settings.bootstrap_owner_email)
        with pytest.raises(AdminServiceError) as exc:
            service.update_user_role(
                current_user=owner_ctx,
                user_id=owner_ctx.user_id,
                role="ADMIN",
            )
        assert exc.value.error_code == "SELF_OPERATION_FORBIDDEN"


def test_phase4_suspend_member_revokes_sessions_and_keys() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()
    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)
        owner_ctx = _build_context(repo, settings.bootstrap_owner_email)

        created = service.create_user(
            current_user=owner_ctx,
            email="member@phase4.local",
            display_name="Member A",
            role="MEMBER",
            org_id=None,
        )
        db.commit()

        key = service.issue_api_key(
            current_user=owner_ctx,
            user_id=created["id"],
            name="member-laptop",
            expires_at=None,
        )
        login = auth_service.login_with_api_key(
            api_key=key.plain_text_key,
            device_info="pytest-phase4",
            ip="127.0.0.1",
            user_agent="pytest",
        )
        db.commit()

        membership = repo.get_membership(user_id=created["id"], org_id=owner_ctx.org_id)
        assert membership is not None
        updated = service.update_member_status(
            current_user=owner_ctx,
            membership_id=membership.id,
            member_status="SUSPENDED",
            reason="policy violation",
        )
        db.commit()

        assert updated["memberStatus"] == "SUSPENDED"
        with pytest.raises(AuthServiceError) as exc:
            auth_service.get_current_user_from_access_token(login.access_token)
        assert exc.value.error_code == "TOKEN_EXPIRED"

        revoked_keys = service.list_api_keys(
            current_user=owner_ctx,
            user_id=created["id"],
            key_status="REVOKED",
            page=1,
            page_size=20,
        )
        assert revoked_keys["total"] >= 1


def test_phase4_reject_cross_org_functional_role_binding() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()
    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)
        owner_ctx = _build_context(repo, settings.bootstrap_owner_email)

        member = service.create_user(
            current_user=owner_ctx,
            email="member2@phase4.local",
            display_name="Member B",
            role="MEMBER",
            org_id=None,
        )
        other_org = repo.get_or_create_organization(org_id="org_other", name="Other Org")
        other_role = repo.create_functional_role(
            org_id=other_org.id,
            code="ops",
            name="运营",
            description="Other org role",
            sort_order=100,
        )
        db.commit()

        member_membership = repo.get_membership(user_id=member["id"], org_id=owner_ctx.org_id)
        assert member_membership is not None

        with pytest.raises(AdminServiceError) as exc:
            service.update_member_functional_role(
                current_user=owner_ctx,
                membership_id=member_membership.id,
                functional_role_id=other_role.id,
                reason="cross-org test",
            )
        assert exc.value.error_code == "FUNCTION_ROLE_MISMATCH"


def test_phase4_functional_role_lifecycle() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()
    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)
        owner_ctx = _build_context(repo, settings.bootstrap_owner_email)

        created = service.create_functional_role(
            current_user=owner_ctx,
            code="pm",
            name="产品经理",
            description="负责需求分析",
        )
        db.commit()
        assert created["code"] == "pm"

        active_list = service.list_functional_roles(
            current_user=owner_ctx,
            is_active=True,
            page=1,
            page_size=20,
        )
        assert any(item["id"] == created["id"] for item in active_list["items"])

        updated = service.update_functional_role_status(
            current_user=owner_ctx,
            role_id=created["id"],
            is_active=False,
        )
        db.commit()
        assert updated["isActive"] is False

        inactive_list = service.list_functional_roles(
            current_user=owner_ctx,
            is_active=False,
            page=1,
            page_size=20,
        )
        assert any(item["id"] == created["id"] for item in inactive_list["items"])
