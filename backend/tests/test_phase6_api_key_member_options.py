from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.db import Base
from app.core.user_context import CurrentUserContext
from app.models import AuditLogModel
from app.repositories import UserRepository
from app.services import AdminServiceError, AdminUserService, AuthService


def _build_session_local():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def _build_settings() -> Settings:
    return Settings(
        jwt_secret="phase6-jwt-secret",
        refresh_token_secret="phase6-refresh-secret",
        csrf_secret="phase6-csrf-secret",
        api_key_pepper="phase6-api-key-pepper",
        bootstrap_owner_email="owner@phase6.local",
        bootstrap_owner_display_name="Phase6 Owner",
        bootstrap_owner_api_key="cpk_test_phase6_bootstrap_owner_key_123456",
        access_token_ttl_seconds=300,
        refresh_token_ttl_seconds=3600,
        default_org_id="org_phase6",
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


def test_phase6_member_options_support_prefix_search() -> None:
    settings = _build_settings()
    SessionLocal = _build_session_local()
    with SessionLocal() as db:
        repo = UserRepository(db)
        auth_service = AuthService(settings=settings, repo=repo)
        auth_service.ensure_bootstrap_identity()
        db.commit()

        service = AdminUserService(repo=repo, api_key_pepper=settings.api_key_pepper)
        owner_ctx = _build_context(repo, settings.bootstrap_owner_email)
        service.create_user(
            current_user=owner_ctx,
            email="member-a@phase6.local",
            display_name="Member A",
            role="MEMBER",
            org_id=None,
        )
        service.create_user(
            current_user=owner_ctx,
            email="member-b@phase6.local",
            display_name="Member B",
            role="MEMBER",
            org_id=None,
        )
        db.commit()

        options = service.list_member_options(
            current_user=owner_ctx,
            query="member-a",
            org_id=None,
            limit=20,
        )
        assert len(options["items"]) == 1
        assert options["items"][0]["email"] == "member-a@phase6.local"
        assert options["items"][0]["orgId"] == owner_ctx.org_id


def test_phase6_issue_api_key_rejects_cross_org_org_id() -> None:
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
            email="cross-org-target@phase6.local",
            display_name="Cross Org Target",
            role="MEMBER",
            org_id=None,
        )
        repo.get_or_create_organization(org_id="org_other", name="Other Org")
        db.commit()

        with pytest.raises(AdminServiceError) as exc:
            service.issue_api_key(
                current_user=owner_ctx,
                user_id=created["id"],
                org_id="org_other",
                name="cross-org-key",
                expires_at=None,
            )
        assert exc.value.error_code == "PERMISSION_DENIED"

        failed = db.execute(
            select(AuditLogModel)
            .where(AuditLogModel.action == "ADMIN_ISSUE_API_KEY", AuditLogModel.result == "FAILED")
            .limit(1)
        ).scalar_one_or_none()
        assert failed is not None


def test_phase6_list_api_keys_contains_user_readable_fields() -> None:
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
            email="list-view@phase6.local",
            display_name="List View User",
            role="MEMBER",
            org_id=None,
        )
        service.issue_api_key(
            current_user=owner_ctx,
            user_id=created["id"],
            name="list-view-key",
            expires_at=None,
        )
        db.commit()

        result = service.list_api_keys(
            current_user=owner_ctx,
            user_id=created["id"],
            org_id=None,
            key_status="ACTIVE",
            page=1,
            page_size=20,
        )
        assert result["total"] >= 1
        item = result["items"][0]
        assert item["userId"] == created["id"]
        assert item["userEmail"] == "list-view@phase6.local"
        assert item["userDisplayName"] == "List View User"
