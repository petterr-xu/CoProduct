from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import secrets

from fastapi import status

from app.core.config import Settings
from app.core.security import (
    SecurityError,
    api_key_prefix,
    api_key_salt,
    compute_expiry,
    decode_jwt_token,
    generate_csrf_token,
    hash_api_key,
    hash_refresh_token,
    issue_jwt_token,
    verify_api_key_hash,
)
from app.core.user_context import CurrentUserContext
from app.models import ApiKeyModel, MembershipModel, UserModel
from app.repositories import UserRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_expired(dt: datetime | None) -> bool:
    if dt is None:
        return False
    value = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return value <= utc_now()


class AuthServiceError(Exception):
    """Expected auth-domain error with API mapping fields."""

    def __init__(self, *, error_code: str, message: str, http_status: int = status.HTTP_401_UNAUTHORIZED) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True)
class AuthLoginResult:
    access_token: str
    refresh_token: str
    csrf_token: str
    expires_in: int
    user: CurrentUserContext


@dataclass(frozen=True)
class AuthRefreshResult:
    access_token: str
    refresh_token: str
    csrf_token: str
    expires_in: int


class AuthService:
    """Authentication service for key login, refresh, logout, and context resolution."""

    def __init__(self, settings: Settings, repo: UserRepository) -> None:
        self.settings = settings
        self.repo = repo

    def ensure_bootstrap_identity(self) -> None:
        """Create default org/owner/api key for first-time deployments."""
        if self.repo.count_users() > 0:
            return

        org = self.repo.get_or_create_organization(org_id=self.settings.default_org_id, name="Default Organization")
        owner = self.repo.create_user(
            email=self.settings.bootstrap_owner_email,
            display_name=self.settings.bootstrap_owner_display_name,
            status="ACTIVE",
        )
        self.repo.create_membership(user_id=owner.id, org_id=org.id, role="OWNER", status="ACTIVE")

        salt = api_key_salt()
        key_hash = hash_api_key(self.settings.bootstrap_owner_api_key, salt=salt, pepper=self.settings.api_key_pepper)
        self.repo.create_api_key(
            user_id=owner.id,
            org_id=org.id,
            name="bootstrap-owner",
            key_prefix=api_key_prefix(self.settings.bootstrap_owner_api_key),
            key_hash=key_hash,
            key_salt=salt,
            expires_at=None,
        )
        self.repo.create_audit_log(
            org_id=org.id,
            actor_user_id=owner.id,
            target_type="user",
            target_id=owner.id,
            action="BOOTSTRAP_OWNER_CREATED",
            result="SUCCESS",
            metadata={"email": owner.email},
        )

    def login_with_api_key(
        self,
        *,
        api_key: str,
        device_info: str | None,
        ip: str | None,
        user_agent: str | None,
    ) -> AuthLoginResult:
        if len(api_key) < 20 or len(api_key) > 128 or not api_key.startswith("cpk_"):
            self._audit_login_failure(reason="invalid_api_key_format", ip=ip, user_agent=user_agent)
            raise AuthServiceError(error_code="AUTH_ERROR", message="Invalid API key")

        key_record = self._find_matching_api_key(api_key)
        if key_record is None:
            self._audit_login_failure(reason="invalid_api_key", ip=ip, user_agent=user_agent)
            raise AuthServiceError(error_code="AUTH_ERROR", message="Invalid API key")

        user, membership = self._load_active_identity(user_id=key_record.user_id, org_id=key_record.org_id)
        session_id = f"as_{secrets.token_hex(6)}"
        csrf_token = generate_csrf_token()

        refresh_token = issue_jwt_token(
            payload={
                "typ": "refresh",
                "sub": user.id,
                "org_id": membership.org_id,
                "sid": session_id,
                "csrf": csrf_token,
            },
            secret=self.settings.refresh_token_secret,
            ttl_seconds=self.settings.refresh_token_ttl_seconds,
        )
        refresh_hash = hash_refresh_token(refresh_token, secret=self.settings.refresh_token_secret)
        refresh_expires_at = compute_expiry(self.settings.refresh_token_ttl_seconds)

        session = self.repo.create_auth_session(
            session_id=session_id,
            user_id=user.id,
            org_id=membership.org_id,
            api_key_id=key_record.id,
            refresh_token_hash=refresh_hash,
            expires_at=refresh_expires_at,
            device_info=device_info,
            ip=ip,
            user_agent=user_agent,
        )

        access_token = self._issue_access_token(
            user=user,
            membership=membership,
            session_id=session.id,
        )
        self.repo.mark_api_key_used(key_record.id)
        self.repo.touch_last_login(user.id)
        self.repo.create_audit_log(
            org_id=membership.org_id,
            actor_user_id=user.id,
            target_type="auth_session",
            target_id=session.id,
            action="AUTH_LOGIN",
            result="SUCCESS",
            metadata={"deviceInfo": device_info},
        )

        return AuthLoginResult(
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
            expires_in=self.settings.access_token_ttl_seconds,
            user=self._to_user_context(user=user, membership=membership, session_id=session.id),
        )

    def refresh_access_token(
        self,
        *,
        refresh_token: str | None,
        csrf_header: str | None,
        csrf_cookie: str | None,
        ip: str | None,
        user_agent: str | None,
    ) -> AuthRefreshResult:
        if not refresh_token:
            raise AuthServiceError(error_code="AUTH_ERROR", message="Missing refresh token")
        if not csrf_header or not csrf_cookie or csrf_header != csrf_cookie:
            raise AuthServiceError(error_code="PERMISSION_DENIED", message="CSRF token mismatch")

        try:
            claims = decode_jwt_token(refresh_token, secret=self.settings.refresh_token_secret)
        except SecurityError as exc:
            raise AuthServiceError(error_code="TOKEN_EXPIRED", message="Invalid refresh token") from exc

        if claims.get("typ") != "refresh":
            raise AuthServiceError(error_code="AUTH_ERROR", message="Invalid refresh token")

        refresh_csrf = claims.get("csrf")
        if not isinstance(refresh_csrf, str) or refresh_csrf != csrf_cookie:
            raise AuthServiceError(error_code="PERMISSION_DENIED", message="CSRF token mismatch")

        session_id = str(claims.get("sid", ""))
        user_id = str(claims.get("sub", ""))
        org_id = str(claims.get("org_id", ""))
        if not session_id or not user_id or not org_id:
            raise AuthServiceError(error_code="AUTH_ERROR", message="Invalid refresh token payload")

        expected_hash = hash_refresh_token(refresh_token, secret=self.settings.refresh_token_secret)
        user, membership = self._load_active_identity(user_id=user_id, org_id=org_id)

        new_csrf = generate_csrf_token()
        new_refresh_token = issue_jwt_token(
            payload={
                "typ": "refresh",
                "sub": user.id,
                "org_id": membership.org_id,
                "sid": session_id,
                "csrf": new_csrf,
            },
            secret=self.settings.refresh_token_secret,
            ttl_seconds=self.settings.refresh_token_ttl_seconds,
        )
        new_refresh_hash = hash_refresh_token(new_refresh_token, secret=self.settings.refresh_token_secret)
        session = self.repo.rotate_auth_session(
            session_id=session_id,
            expected_refresh_hash=expected_hash,
            new_refresh_hash=new_refresh_hash,
            new_expires_at=compute_expiry(self.settings.refresh_token_ttl_seconds),
        )
        if session is None:
            self.repo.create_audit_log(
                org_id=org_id,
                actor_user_id=user_id,
                target_type="auth_session",
                target_id=session_id,
                action="AUTH_REFRESH",
                result="FAILED",
                metadata={"reason": "refresh_replay_or_revoked", "ip": ip},
            )
            raise AuthServiceError(error_code="TOKEN_EXPIRED", message="Refresh token expired")

        access_token = self._issue_access_token(user=user, membership=membership, session_id=session.id)
        self.repo.create_audit_log(
            org_id=org_id,
            actor_user_id=user_id,
            target_type="auth_session",
            target_id=session_id,
            action="AUTH_REFRESH",
            result="SUCCESS",
            metadata={"ip": ip, "userAgent": user_agent},
        )
        return AuthRefreshResult(
            access_token=access_token,
            refresh_token=new_refresh_token,
            csrf_token=new_csrf,
            expires_in=self.settings.access_token_ttl_seconds,
        )

    def logout(self, *, refresh_token: str | None, current_user: CurrentUserContext, all_devices: bool = False) -> None:
        if all_devices:
            revoked = self.repo.revoke_all_user_sessions(user_id=current_user.user_id, org_id=current_user.org_id)
            self.repo.create_audit_log(
                org_id=current_user.org_id,
                actor_user_id=current_user.user_id,
                target_type="auth_session",
                target_id=None,
                action="AUTH_LOGOUT_ALL",
                result="SUCCESS",
                metadata={"revokedCount": revoked},
            )
            return

        if not refresh_token:
            raise AuthServiceError(error_code="AUTH_ERROR", message="Missing refresh token")

        try:
            claims = decode_jwt_token(refresh_token, secret=self.settings.refresh_token_secret)
        except SecurityError as exc:
            raise AuthServiceError(error_code="TOKEN_EXPIRED", message="Invalid refresh token") from exc

        session_id = str(claims.get("sid", ""))
        if not session_id:
            raise AuthServiceError(error_code="AUTH_ERROR", message="Invalid refresh token payload")
        self.repo.revoke_auth_session(session_id)
        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="auth_session",
            target_id=session_id,
            action="AUTH_LOGOUT",
            result="SUCCESS",
            metadata={"allDevices": False},
        )

    def get_current_user_from_access_token(self, access_token: str) -> CurrentUserContext:
        try:
            claims = decode_jwt_token(access_token, secret=self.settings.jwt_secret)
        except SecurityError as exc:
            raise AuthServiceError(error_code="TOKEN_EXPIRED", message="Access token expired") from exc

        if claims.get("typ") != "access":
            raise AuthServiceError(error_code="AUTH_ERROR", message="Invalid access token")

        user_id = str(claims.get("sub", ""))
        org_id = str(claims.get("org_id", ""))
        session_id = str(claims.get("sid", ""))
        role_from_claim = str(claims.get("role", ""))
        if not user_id or not org_id:
            raise AuthServiceError(error_code="AUTH_ERROR", message="Invalid access token payload")

        session = self.repo.get_auth_session(session_id)
        if session is None or session.status != "ACTIVE" or is_expired(session.expires_at):
            raise AuthServiceError(error_code="TOKEN_EXPIRED", message="Session expired")

        user, membership = self._load_active_identity(user_id=user_id, org_id=org_id)
        if role_from_claim and role_from_claim != membership.role:
            # membership changed after token issued; keep server-side role as source of truth
            pass
        return self._to_user_context(user=user, membership=membership, session_id=session_id)

    def _issue_access_token(self, *, user: UserModel, membership: MembershipModel, session_id: str) -> str:
        return issue_jwt_token(
            payload={
                "typ": "access",
                "sub": user.id,
                "org_id": membership.org_id,
                "role": membership.role,
                "sid": session_id,
            },
            secret=self.settings.jwt_secret,
            ttl_seconds=self.settings.access_token_ttl_seconds,
        )

    def _load_active_identity(self, *, user_id: str, org_id: str) -> tuple[UserModel, MembershipModel]:
        user = self.repo.get_user(user_id)
        if user is None or user.status != "ACTIVE":
            raise AuthServiceError(error_code="USER_DISABLED", message="User is disabled")

        membership = self.repo.get_active_membership(user_id=user.id, org_id=org_id)
        if membership is None:
            raise AuthServiceError(error_code="PERMISSION_DENIED", message="No active organization membership")
        return user, membership

    def _find_matching_api_key(self, raw_api_key: str) -> ApiKeyModel | None:
        candidates = self.repo.find_api_keys_by_prefix(api_key_prefix(raw_api_key))
        for item in candidates:
            if item.status != "ACTIVE":
                continue
            if item.expires_at is not None and is_expired(item.expires_at):
                continue
            if verify_api_key_hash(
                raw_api_key,
                salt=item.key_salt,
                pepper=self.settings.api_key_pepper,
                expected_hash=item.key_hash,
            ):
                return item
        return None

    def _audit_login_failure(self, *, reason: str, ip: str | None, user_agent: str | None) -> None:
        self.repo.create_audit_log(
            org_id=None,
            actor_user_id=None,
            target_type="auth_session",
            target_id=None,
            action="AUTH_LOGIN",
            result="FAILED",
            metadata={"reason": reason, "ip": ip, "userAgent": user_agent},
        )

    @staticmethod
    def _to_user_context(*, user: UserModel, membership: MembershipModel, session_id: str | None) -> CurrentUserContext:
        return CurrentUserContext(
            user_id=user.id,
            org_id=membership.org_id,
            role=membership.role,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            session_id=session_id,
        )
