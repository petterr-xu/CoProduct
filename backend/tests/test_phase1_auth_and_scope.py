from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.db import Base
from app.core.security import api_key_prefix
from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository, UserRepository
from app.services import AuthService, AuthServiceError, HistoryService


def _build_session_local():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def test_auth_service_login_refresh_and_replay_protection() -> None:
    settings = Settings(
        jwt_secret="test-jwt-secret",
        refresh_token_secret="test-refresh-secret",
        csrf_secret="test-csrf-secret",
        api_key_pepper="test-api-key-pepper",
        bootstrap_owner_email="owner@test.local",
        bootstrap_owner_display_name="Owner",
        bootstrap_owner_api_key="cpk_test_bootstrap_owner_key_123456",
        access_token_ttl_seconds=300,
        refresh_token_ttl_seconds=3600,
        default_org_id="org_test",
    )
    SessionLocal = _build_session_local()

    with SessionLocal() as db:
        user_repo = UserRepository(db)
        auth = AuthService(settings=settings, repo=user_repo)
        auth.ensure_bootstrap_identity()
        db.commit()

        login = auth.login_with_api_key(
            api_key=settings.bootstrap_owner_api_key,
            device_info="pytest",
            ip="127.0.0.1",
            user_agent="pytest",
        )
        db.commit()

        assert login.user.role == "OWNER"
        assert login.user.org_id == "org_test"

        me = auth.get_current_user_from_access_token(login.access_token)
        assert me.user_id == login.user.user_id

        refreshed = auth.refresh_access_token(
            refresh_token=login.refresh_token,
            csrf_header=login.csrf_token,
            csrf_cookie=login.csrf_token,
            ip="127.0.0.1",
            user_agent="pytest",
        )
        db.commit()
        assert refreshed.access_token
        assert refreshed.refresh_token != login.refresh_token

        try:
            auth.refresh_access_token(
                refresh_token=login.refresh_token,
                csrf_header=login.csrf_token,
                csrf_cookie=login.csrf_token,
                ip="127.0.0.1",
                user_agent="pytest",
            )
        except AuthServiceError as exc:
            assert exc.error_code == "TOKEN_EXPIRED"
        else:
            raise AssertionError("Expected replay-protection failure for reused refresh token")


def test_history_scope_member_only_sees_own_records() -> None:
    SessionLocal = _build_session_local()
    with SessionLocal() as db:
        user_repo = UserRepository(db)
        org = user_repo.get_or_create_organization(org_id="org_1", name="Org 1")
        owner = user_repo.create_user(email="owner@x.dev", display_name="Owner", status="ACTIVE")
        member = user_repo.create_user(email="member@x.dev", display_name="Member", status="ACTIVE")
        user_repo.create_membership(user_id=owner.id, org_id=org.id, role="OWNER", status="ACTIVE")
        user_repo.create_membership(user_id=member.id, org_id=org.id, role="MEMBER", status="ACTIVE")

        repo = PreReviewRepository(db)
        history = HistoryService(repo)

        req_owner = repo.create_request(
            "owner request",
            None,
            None,
            None,
            org_id=org.id,
            created_by_user_id=owner.id,
        )
        ses_owner = repo.create_session(
            request_id=req_owner.id,
            parent_session_id=None,
            version=1,
            status="DONE",
            org_id=org.id,
            created_by_user_id=owner.id,
        )
        repo.upsert_report(
            session_id=ses_owner.id,
            summary="owner",
            capability_status="SUPPORTED",
            report_json={"summary": "owner"},
        )

        req_member = repo.create_request(
            "member request",
            None,
            None,
            None,
            org_id=org.id,
            created_by_user_id=member.id,
        )
        ses_member = repo.create_session(
            request_id=req_member.id,
            parent_session_id=None,
            version=1,
            status="DONE",
            org_id=org.id,
            created_by_user_id=member.id,
        )
        repo.upsert_report(
            session_id=ses_member.id,
            summary="member",
            capability_status="PARTIALLY_SUPPORTED",
            report_json={"summary": "member"},
        )
        db.commit()

        member_context = CurrentUserContext(
            user_id=member.id,
            org_id=org.id,
            role="MEMBER",
            email=member.email,
            display_name=member.display_name,
            status="ACTIVE",
            session_id=None,
        )
        owner_context = CurrentUserContext(
            user_id=owner.id,
            org_id=org.id,
            role="OWNER",
            email=owner.email,
            display_name=owner.display_name,
            status="ACTIVE",
            session_id=None,
        )

        member_view = history.list_history(
            keyword=None,
            capability_status=None,
            page=1,
            page_size=20,
            current_user=member_context,
        )
        owner_view = history.list_history(
            keyword=None,
            capability_status=None,
            page=1,
            page_size=20,
            current_user=owner_context,
        )

        assert member_view["total"] == 1
        assert member_view["items"][0]["requestText"] == "member request"
        assert owner_view["total"] == 2


def test_bootstrap_api_key_is_reconciled_after_revoke() -> None:
    settings = Settings(
        jwt_secret="test-jwt-secret",
        refresh_token_secret="test-refresh-secret",
        csrf_secret="test-csrf-secret",
        api_key_pepper="test-api-key-pepper",
        bootstrap_owner_email="owner@test.local",
        bootstrap_owner_display_name="Owner",
        bootstrap_owner_api_key="cpk_test_bootstrap_owner_key_123456",
        access_token_ttl_seconds=300,
        refresh_token_ttl_seconds=3600,
        default_org_id="org_test",
    )
    SessionLocal = _build_session_local()

    with SessionLocal() as db:
        user_repo = UserRepository(db)
        auth = AuthService(settings=settings, repo=user_repo)
        auth.ensure_bootstrap_identity()
        db.commit()

        keys = user_repo.find_api_keys_by_prefix(api_key_prefix(settings.bootstrap_owner_api_key))
        assert keys
        user_repo.revoke_api_key_and_sessions(key_id=keys[0].id, org_id=settings.default_org_id)
        db.commit()

        try:
            auth.login_with_api_key(
                api_key=settings.bootstrap_owner_api_key,
                device_info="pytest",
                ip="127.0.0.1",
                user_agent="pytest",
            )
        except AuthServiceError as exc:
            assert exc.error_code == "AUTH_ERROR"
        else:
            raise AssertionError("Expected login failure after bootstrap key revoke")

        auth.ensure_bootstrap_identity()
        db.commit()

        restored_login = auth.login_with_api_key(
            api_key=settings.bootstrap_owner_api_key,
            device_info="pytest-retry",
            ip="127.0.0.1",
            user_agent="pytest",
        )
        db.commit()
        assert restored_login.user.org_id == settings.default_org_id
