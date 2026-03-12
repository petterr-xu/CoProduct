from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import status

from app.core.security import api_key_prefix, api_key_salt, generate_api_key, hash_api_key
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository

VALID_ROLES = {"OWNER", "ADMIN", "MEMBER", "VIEWER"}
VALID_USER_STATUS = {"ACTIVE", "DISABLED", "PENDING_INVITE"}
VALID_API_KEY_STATUS = {"ACTIVE", "REVOKED", "EXPIRED"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AdminServiceError(Exception):
    """Expected admin-domain error with API mapping fields."""

    def __init__(self, *, error_code: str, message: str, http_status: int) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True)
class IssueApiKeyResult:
    key_id: str
    key_prefix: str
    plain_text_key: str
    expires_at: str | None


class AdminUserService:
    """Admin operations for users, API keys, and audit logs."""

    def __init__(self, *, repo: UserRepository, api_key_pepper: str) -> None:
        self.repo = repo
        self.api_key_pepper = api_key_pepper

    def list_users(
        self,
        *,
        current_user: CurrentUserContext,
        query: str | None,
        role: str | None,
        user_status: str | None,
        page: int,
        page_size: int,
    ) -> dict:
        if role and role not in VALID_ROLES:
            raise AdminServiceError(
                error_code="VALIDATION_ERROR",
                message=f"Invalid role: {role}",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if user_status and user_status not in VALID_USER_STATUS:
            raise AdminServiceError(
                error_code="VALIDATION_ERROR",
                message=f"Invalid user status: {user_status}",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        total, items = self.repo.list_users(
            org_id=current_user.org_id,
            query=query,
            role=role,
            status=user_status,
            page=page,
            page_size=page_size,
        )
        return {"items": items, "total": total, "page": page, "pageSize": page_size}

    def create_user(
        self,
        *,
        current_user: CurrentUserContext,
        email: str,
        display_name: str,
        role: str,
        org_id: str | None,
    ) -> dict:
        target_org_id = org_id or current_user.org_id
        if target_org_id != current_user.org_id:
            raise AdminServiceError(
                error_code="PERMISSION_DENIED",
                message="Cannot create users in another organization",
                http_status=status.HTTP_403_FORBIDDEN,
            )
        if role not in VALID_ROLES:
            raise AdminServiceError(
                error_code="VALIDATION_ERROR",
                message=f"Invalid role: {role}",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        normalized_email = email.strip().lower()
        if not normalized_email or "@" not in normalized_email:
            raise AdminServiceError(
                error_code="VALIDATION_ERROR",
                message="Invalid email",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        user = self.repo.get_user_by_email(normalized_email)
        if user is None:
            user = self.repo.create_user(email=normalized_email, display_name=display_name.strip(), status="ACTIVE")
        else:
            membership = self.repo.get_membership(user_id=user.id, org_id=target_org_id)
            if membership is not None:
                raise AdminServiceError(
                    error_code="VALIDATION_ERROR",
                    message="User already exists in this organization",
                    http_status=status.HTTP_409_CONFLICT,
                )

        membership = self.repo.create_membership(user_id=user.id, org_id=target_org_id, role=role, status="ACTIVE")
        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="user",
            target_id=user.id,
            action="ADMIN_CREATE_USER",
            result="SUCCESS",
            metadata={"role": role, "email": normalized_email},
        )
        return {
            "id": user.id,
            "email": user.email,
            "displayName": user.display_name,
            "role": membership.role,
            "status": user.status,
            "orgId": membership.org_id,
            "createdAt": user.created_at.isoformat() if user.created_at else "",
            "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
        }

    def update_user_status(
        self,
        *,
        current_user: CurrentUserContext,
        user_id: str,
        next_status: str,
    ) -> dict:
        if next_status not in VALID_USER_STATUS:
            raise AdminServiceError(
                error_code="VALIDATION_ERROR",
                message=f"Invalid user status: {next_status}",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        membership = self.repo.get_membership(user_id=user_id, org_id=current_user.org_id)
        if membership is None:
            raise AdminServiceError(
                error_code="RESOURCE_NOT_FOUND",
                message="User membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        user = self.repo.update_user_status(user_id=user_id, status=next_status)
        if user is None:
            raise AdminServiceError(
                error_code="RESOURCE_NOT_FOUND",
                message="User not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        revoked = 0
        if next_status == "DISABLED":
            revoked = self.repo.revoke_all_user_sessions(user_id=user_id, org_id=current_user.org_id)

        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="user",
            target_id=user_id,
            action="ADMIN_UPDATE_USER_STATUS",
            result="SUCCESS",
            metadata={"status": next_status, "revokedSessions": revoked},
        )
        return {
            "id": user.id,
            "email": user.email,
            "displayName": user.display_name,
            "role": membership.role,
            "status": user.status,
            "orgId": membership.org_id,
            "createdAt": user.created_at.isoformat() if user.created_at else "",
            "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
        }

    def update_user_role(
        self,
        *,
        current_user: CurrentUserContext,
        user_id: str,
        role: str,
    ) -> dict:
        if role not in VALID_ROLES:
            raise AdminServiceError(
                error_code="VALIDATION_ERROR",
                message=f"Invalid role: {role}",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        membership = self.repo.update_membership_role(user_id=user_id, org_id=current_user.org_id, role=role)
        if membership is None:
            raise AdminServiceError(
                error_code="RESOURCE_NOT_FOUND",
                message="User membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        user = self.repo.get_user(user_id)
        if user is None:
            raise AdminServiceError(
                error_code="RESOURCE_NOT_FOUND",
                message="User not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="user",
            target_id=user_id,
            action="ADMIN_UPDATE_USER_ROLE",
            result="SUCCESS",
            metadata={"role": role},
        )
        return {
            "id": user.id,
            "email": user.email,
            "displayName": user.display_name,
            "role": membership.role,
            "status": user.status,
            "orgId": membership.org_id,
            "createdAt": user.created_at.isoformat() if user.created_at else "",
            "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
        }

    def issue_api_key(
        self,
        *,
        current_user: CurrentUserContext,
        user_id: str,
        name: str,
        expires_at: datetime | None,
    ) -> IssueApiKeyResult:
        if not name.strip():
            raise AdminServiceError(
                error_code="VALIDATION_ERROR",
                message="API key name is required",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        membership = self.repo.get_membership(user_id=user_id, org_id=current_user.org_id)
        if membership is None:
            raise AdminServiceError(
                error_code="RESOURCE_NOT_FOUND",
                message="User membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        user = self.repo.get_user(user_id)
        if user is None:
            raise AdminServiceError(
                error_code="RESOURCE_NOT_FOUND",
                message="User not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        plain_text_key = generate_api_key(prefix="cpk_live")
        key_prefix = api_key_prefix(plain_text_key)
        salt = api_key_salt()
        key_hash = hash_api_key(plain_text_key, salt=salt, pepper=self.api_key_pepper)

        key = self.repo.create_api_key(
            user_id=user_id,
            org_id=current_user.org_id,
            name=name.strip(),
            key_prefix=key_prefix,
            key_hash=key_hash,
            key_salt=salt,
            expires_at=expires_at,
        )
        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="api_key",
            target_id=key.id,
            action="ADMIN_ISSUE_API_KEY",
            result="SUCCESS",
            metadata={"userId": user_id, "name": key.name},
        )
        return IssueApiKeyResult(
            key_id=key.id,
            key_prefix=key.key_prefix,
            plain_text_key=plain_text_key,
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
        )

    def list_api_keys(
        self,
        *,
        current_user: CurrentUserContext,
        user_id: str | None,
        key_status: str | None,
        page: int,
        page_size: int,
    ) -> dict:
        if key_status and key_status not in VALID_API_KEY_STATUS:
            raise AdminServiceError(
                error_code="VALIDATION_ERROR",
                message=f"Invalid API key status: {key_status}",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        total, items = self.repo.list_api_keys(
            org_id=current_user.org_id,
            user_id=user_id,
            status=key_status,
            page=page,
            page_size=page_size,
        )
        return {"items": items, "total": total, "page": page, "pageSize": page_size}

    def revoke_api_key(self, *, current_user: CurrentUserContext, key_id: str) -> dict:
        api_key, revoked_sessions = self.repo.revoke_api_key_and_sessions(key_id=key_id, org_id=current_user.org_id)
        if api_key is None:
            raise AdminServiceError(
                error_code="RESOURCE_NOT_FOUND",
                message="API key not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="api_key",
            target_id=key_id,
            action="ADMIN_REVOKE_API_KEY",
            result="SUCCESS",
            metadata={"revokedSessions": revoked_sessions},
        )
        return {"success": True, "revokedSessions": revoked_sessions}

    def list_audit_logs(
        self,
        *,
        current_user: CurrentUserContext,
        actor_user_id: str | None,
        action: str | None,
        page: int,
        page_size: int,
    ) -> dict:
        total, items = self.repo.list_audit_logs(
            org_id=current_user.org_id,
            actor_user_id=actor_user_id,
            action=action,
            page=page,
            page_size=page_size,
        )
        return {"items": items, "total": total, "page": page, "pageSize": page_size}
