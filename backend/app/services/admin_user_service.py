from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import status

from app.core.security import api_key_prefix, api_key_salt, generate_api_key, hash_api_key
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository

VALID_ROLES = {"OWNER", "ADMIN", "MEMBER", "VIEWER"}
VALID_USER_STATUS = {"ACTIVE", "DISABLED", "PENDING_INVITE"}
VALID_MEMBER_STATUS = {"INVITED", "ACTIVE", "SUSPENDED", "REMOVED"}
VALID_API_KEY_STATUS = {"ACTIVE", "REVOKED", "EXPIRED"}
FUNCTION_ROLE_CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")


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
    """Admin operations for users, members, API keys, functional roles, and audit logs."""

    def __init__(self, *, repo: UserRepository, api_key_pepper: str) -> None:
        self.repo = repo
        self.api_key_pepper = api_key_pepper

    @staticmethod
    def _build_user_item(*, user, membership) -> dict:
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

    def _raise(self, *, error_code: str, message: str, http_status: int) -> None:
        raise AdminServiceError(error_code=error_code, message=message, http_status=http_status)

    def _raise_with_audit(
        self,
        *,
        current_user: CurrentUserContext,
        action: str,
        target_type: str,
        target_id: str | None,
        error_code: str,
        message: str,
        http_status: int,
        metadata: dict | None = None,
    ) -> None:
        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type=target_type,
            target_id=target_id,
            action=action,
            result="FAILED",
            metadata={
                "errorCode": error_code,
                "message": message,
                **(metadata or {}),
            },
        )
        self._raise(error_code=error_code, message=message, http_status=http_status)

    def _ensure_can_manage_target_membership(
        self,
        *,
        current_user: CurrentUserContext,
        action: str,
        target_membership,
        target_id: str,
    ) -> None:
        if current_user.role not in {"OWNER", "ADMIN"}:
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="user",
                target_id=target_id,
                error_code="PERMISSION_DENIED",
                message="Admin permission required",
                http_status=status.HTTP_403_FORBIDDEN,
            )

        if current_user.role == "ADMIN" and target_membership.role == "OWNER":
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="user",
                target_id=target_id,
                error_code="OWNER_GUARD_VIOLATION",
                message="ADMIN cannot operate OWNER membership",
                http_status=status.HTTP_403_FORBIDDEN,
            )

    def _ensure_self_operation_allowed(
        self,
        *,
        current_user: CurrentUserContext,
        action: str,
        target_user_id: str,
        next_role: str | None = None,
        next_user_status: str | None = None,
        next_member_status: str | None = None,
    ) -> None:
        if current_user.user_id != target_user_id:
            return

        if next_role is not None and next_role != current_user.role:
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="user",
                target_id=target_user_id,
                error_code="SELF_OPERATION_FORBIDDEN",
                message="Cannot change current user's own role",
                http_status=status.HTTP_403_FORBIDDEN,
                metadata={"nextRole": next_role},
            )

        if next_user_status is not None and next_user_status != "ACTIVE":
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="user",
                target_id=target_user_id,
                error_code="SELF_OPERATION_FORBIDDEN",
                message="Cannot disable current user account",
                http_status=status.HTTP_403_FORBIDDEN,
                metadata={"nextStatus": next_user_status},
            )

        if next_member_status is not None and next_member_status != "ACTIVE":
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="membership",
                target_id=target_user_id,
                error_code="SELF_OPERATION_FORBIDDEN",
                message="Cannot inactivate current membership",
                http_status=status.HTTP_403_FORBIDDEN,
                metadata={"nextMemberStatus": next_member_status},
            )

    def _ensure_owner_floor(
        self,
        *,
        current_user: CurrentUserContext,
        action: str,
        target_membership,
        target_id: str,
        next_role: str | None = None,
        next_user_status: str | None = None,
        next_member_status: str | None = None,
    ) -> None:
        if target_membership.role != "OWNER":
            return

        owner_will_be_inactive = (
            (next_role is not None and next_role != "OWNER")
            or (next_user_status is not None and next_user_status != "ACTIVE")
            or (next_member_status is not None and next_member_status != "ACTIVE")
        )
        if not owner_will_be_inactive:
            return

        active_owner_count = self.repo.count_active_owners(org_id=current_user.org_id)
        if active_owner_count <= 1:
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="membership",
                target_id=target_id,
                error_code="LAST_OWNER_PROTECTED",
                message="At least one ACTIVE OWNER must remain in organization",
                http_status=status.HTTP_409_CONFLICT,
            )

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
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid role: {role}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        if user_status and user_status not in VALID_USER_STATUS:
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid user status: {user_status}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
            self._raise(
                error_code="PERMISSION_DENIED",
                message="Cannot create users in another organization",
                http_status=status.HTTP_403_FORBIDDEN,
            )
        if role not in VALID_ROLES:
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid role: {role}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        if current_user.role == "ADMIN" and role == "OWNER":
            self._raise_with_audit(
                current_user=current_user,
                action="ADMIN_CREATE_USER",
                target_type="user",
                target_id=None,
                error_code="OWNER_GUARD_VIOLATION",
                message="ADMIN cannot create OWNER user",
                http_status=status.HTTP_403_FORBIDDEN,
            )

        normalized_email = email.strip().lower()
        if not normalized_email or "@" not in normalized_email:
            self._raise(
                error_code="VALIDATION_ERROR",
                message="Invalid email",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        user = self.repo.get_user_by_email(normalized_email)
        if user is None:
            user = self.repo.create_user(email=normalized_email, display_name=display_name.strip(), status="ACTIVE")
        else:
            membership = self.repo.get_membership(user_id=user.id, org_id=target_org_id)
            if membership is not None:
                self._raise(
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
        return self._build_user_item(user=user, membership=membership)

    def update_user_status(
        self,
        *,
        current_user: CurrentUserContext,
        user_id: str,
        next_status: str,
    ) -> dict:
        action = "ADMIN_UPDATE_USER_STATUS"
        if next_status not in VALID_USER_STATUS:
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid user status: {next_status}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        membership = self.repo.get_membership(user_id=user_id, org_id=current_user.org_id)
        if membership is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        self._ensure_can_manage_target_membership(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=user_id,
        )
        self._ensure_self_operation_allowed(
            current_user=current_user,
            action=action,
            target_user_id=user_id,
            next_user_status=next_status,
        )
        self._ensure_owner_floor(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=membership.id,
            next_user_status=next_status,
        )

        user = self.repo.update_user_status(user_id=user_id, status=next_status)
        if user is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        revoked_sessions = 0
        revoked_keys = 0
        if next_status == "DISABLED":
            revoked_sessions = self.repo.revoke_all_user_sessions(user_id=user_id, org_id=current_user.org_id)
            revoked_keys = self.repo.revoke_active_api_keys_by_user(user_id=user_id, org_id=current_user.org_id)

        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="user",
            target_id=user_id,
            action=action,
            result="SUCCESS",
            metadata={
                "status": next_status,
                "revokedSessions": revoked_sessions,
                "revokedKeys": revoked_keys,
            },
        )
        return self._build_user_item(user=user, membership=membership)

    def update_user_role(
        self,
        *,
        current_user: CurrentUserContext,
        user_id: str,
        role: str,
    ) -> dict:
        action = "ADMIN_UPDATE_USER_ROLE"
        if role not in VALID_ROLES:
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid role: {role}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        membership = self.repo.get_membership(user_id=user_id, org_id=current_user.org_id)
        if membership is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        user = self.repo.get_user(user_id)
        if user is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        self._ensure_can_manage_target_membership(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=user_id,
        )
        if current_user.role == "ADMIN" and role == "OWNER":
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="user",
                target_id=user_id,
                error_code="OWNER_GUARD_VIOLATION",
                message="ADMIN cannot assign OWNER role",
                http_status=status.HTTP_403_FORBIDDEN,
            )
        self._ensure_self_operation_allowed(
            current_user=current_user,
            action=action,
            target_user_id=user_id,
            next_role=role,
        )
        self._ensure_owner_floor(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=membership.id,
            next_role=role,
        )

        updated = self.repo.update_membership_role(user_id=user_id, org_id=current_user.org_id, role=role)
        if updated is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="user",
            target_id=user_id,
            action=action,
            result="SUCCESS",
            metadata={"role": role},
        )
        return self._build_user_item(user=user, membership=updated)

    def issue_api_key(
        self,
        *,
        current_user: CurrentUserContext,
        user_id: str,
        name: str,
        expires_at: datetime | None,
    ) -> IssueApiKeyResult:
        action = "ADMIN_ISSUE_API_KEY"
        if not name.strip():
            self._raise(
                error_code="VALIDATION_ERROR",
                message="API key name is required",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        membership = self.repo.get_membership(user_id=user_id, org_id=current_user.org_id)
        if membership is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        user = self.repo.get_user(user_id)
        if user is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        self._ensure_can_manage_target_membership(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=user_id,
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
            action=action,
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
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid API key status: {key_status}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
        action = "ADMIN_REVOKE_API_KEY"
        api_key = self.repo.get_api_key(key_id)
        if api_key is None or api_key.org_id != current_user.org_id:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="API key not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        membership = self.repo.get_membership(user_id=api_key.user_id, org_id=current_user.org_id)
        if membership is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        self._ensure_can_manage_target_membership(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=api_key.user_id,
        )

        _, revoked_sessions = self.repo.revoke_api_key_and_sessions(key_id=key_id, org_id=current_user.org_id)
        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="api_key",
            target_id=key_id,
            action=action,
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

    def list_members(
        self,
        *,
        current_user: CurrentUserContext,
        query: str | None,
        permission_role: str | None,
        member_status: str | None,
        functional_role_id: str | None,
        page: int,
        page_size: int,
    ) -> dict:
        if permission_role and permission_role not in VALID_ROLES:
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid role: {permission_role}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        if member_status and member_status not in VALID_MEMBER_STATUS:
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid member status: {member_status}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        total, items = self.repo.list_members(
            org_id=current_user.org_id,
            query=query,
            permission_role=permission_role,
            member_status=member_status,
            functional_role_id=functional_role_id,
            page=page,
            page_size=page_size,
        )
        return {"items": items, "total": total, "page": page, "pageSize": page_size}

    def update_member_role(
        self,
        *,
        current_user: CurrentUserContext,
        membership_id: str,
        role: str,
        reason: str | None,
    ) -> dict:
        action = "ADMIN_UPDATE_MEMBER_ROLE"
        if role not in VALID_ROLES:
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid role: {role}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        membership = self.repo.get_membership_by_id(membership_id)
        if membership is None or membership.org_id != current_user.org_id:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        user = self.repo.get_user(membership.user_id)
        if user is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="User not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        self._ensure_can_manage_target_membership(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=membership.user_id,
        )
        if current_user.role == "ADMIN" and role == "OWNER":
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="membership",
                target_id=membership_id,
                error_code="OWNER_GUARD_VIOLATION",
                message="ADMIN cannot assign OWNER role",
                http_status=status.HTTP_403_FORBIDDEN,
            )
        self._ensure_self_operation_allowed(
            current_user=current_user,
            action=action,
            target_user_id=membership.user_id,
            next_role=role,
        )
        self._ensure_owner_floor(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=membership_id,
            next_role=role,
        )

        before_role = membership.role
        updated = self.repo.update_membership_role_by_id(membership_id=membership_id, role=role)
        if updated is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        item = self.repo.get_member_item(membership_id=membership_id)
        if item is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="membership",
            target_id=membership_id,
            action=action,
            result="SUCCESS",
            metadata={"beforeRole": before_role, "afterRole": updated.role, "reason": reason},
        )
        return item

    def update_member_status(
        self,
        *,
        current_user: CurrentUserContext,
        membership_id: str,
        member_status: str,
        reason: str | None,
    ) -> dict:
        action = "ADMIN_UPDATE_MEMBER_STATUS"
        if member_status not in VALID_MEMBER_STATUS:
            self._raise(
                error_code="VALIDATION_ERROR",
                message=f"Invalid member status: {member_status}",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        membership = self.repo.get_membership_by_id(membership_id)
        if membership is None or membership.org_id != current_user.org_id:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        self._ensure_can_manage_target_membership(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=membership.user_id,
        )
        self._ensure_self_operation_allowed(
            current_user=current_user,
            action=action,
            target_user_id=membership.user_id,
            next_member_status=member_status,
        )
        self._ensure_owner_floor(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=membership_id,
            next_member_status=member_status,
        )

        before_status = membership.status
        updated = self.repo.update_membership_status_by_id(membership_id=membership_id, member_status=member_status)
        if updated is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        revoked_sessions = 0
        revoked_keys = 0
        if member_status != "ACTIVE":
            revoked_sessions = self.repo.revoke_all_user_sessions(user_id=membership.user_id, org_id=membership.org_id)
            revoked_keys = self.repo.revoke_active_api_keys_by_user(user_id=membership.user_id, org_id=membership.org_id)

        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="membership",
            target_id=membership_id,
            action=action,
            result="SUCCESS",
            metadata={
                "beforeStatus": before_status,
                "afterStatus": updated.status,
                "reason": reason,
                "revokedSessions": revoked_sessions,
                "revokedKeys": revoked_keys,
            },
        )

        item = self.repo.get_member_item(membership_id=membership_id)
        if item is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return item

    def update_member_functional_role(
        self,
        *,
        current_user: CurrentUserContext,
        membership_id: str,
        functional_role_id: str,
        reason: str | None,
    ) -> dict:
        action = "ADMIN_UPDATE_MEMBER_FUNCTION_ROLE"
        membership = self.repo.get_membership_by_id(membership_id)
        if membership is None or membership.org_id != current_user.org_id:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        self._ensure_can_manage_target_membership(
            current_user=current_user,
            action=action,
            target_membership=membership,
            target_id=membership.user_id,
        )

        function_role = self.repo.get_functional_role(functional_role_id)
        if function_role is None or function_role.org_id != current_user.org_id:
            self._raise_with_audit(
                current_user=current_user,
                action=action,
                target_type="membership",
                target_id=membership_id,
                error_code="FUNCTION_ROLE_MISMATCH",
                message="Functional role does not belong to current organization",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        if not function_role.is_active:
            self._raise(
                error_code="VALIDATION_ERROR",
                message="Functional role is inactive",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        previous_role_id = membership.functional_role_id
        updated = self.repo.update_membership_functional_role_by_id(
            membership_id=membership_id,
            functional_role_id=functional_role_id,
        )
        if updated is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="membership",
            target_id=membership_id,
            action=action,
            result="SUCCESS",
            metadata={
                "beforeFunctionalRoleId": previous_role_id,
                "afterFunctionalRoleId": functional_role_id,
                "reason": reason,
            },
        )
        item = self.repo.get_member_item(membership_id=membership_id)
        if item is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Membership not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return item

    def list_functional_roles(
        self,
        *,
        current_user: CurrentUserContext,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> dict:
        total, items = self.repo.list_functional_roles(
            org_id=current_user.org_id,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )
        return {"items": items, "total": total, "page": page, "pageSize": page_size}

    def create_functional_role(
        self,
        *,
        current_user: CurrentUserContext,
        code: str,
        name: str,
        description: str | None,
    ) -> dict:
        normalized_code = code.strip().lower()
        if not FUNCTION_ROLE_CODE_PATTERN.match(normalized_code):
            self._raise(
                error_code="VALIDATION_ERROR",
                message="Invalid functional role code",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        normalized_name = name.strip()
        if not normalized_name:
            self._raise(
                error_code="VALIDATION_ERROR",
                message="Functional role name is required",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        existing = self.repo.find_functional_role_by_code(org_id=current_user.org_id, code=normalized_code)
        if existing is not None:
            self._raise(
                error_code="VALIDATION_ERROR",
                message="Functional role code already exists",
                http_status=status.HTTP_409_CONFLICT,
            )

        item = self.repo.create_functional_role(
            org_id=current_user.org_id,
            code=normalized_code,
            name=normalized_name,
            description=description.strip() if description else None,
            sort_order=100,
        )
        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="functional_role",
            target_id=item.id,
            action="ADMIN_CREATE_FUNCTION_ROLE",
            result="SUCCESS",
            metadata={"code": item.code, "name": item.name},
        )
        return {
            "id": item.id,
            "orgId": item.org_id,
            "code": item.code,
            "name": item.name,
            "description": item.description,
            "isActive": item.is_active,
            "sortOrder": item.sort_order,
            "createdAt": item.created_at.isoformat() if item.created_at else "",
            "updatedAt": item.updated_at.isoformat() if item.updated_at else "",
        }

    def update_functional_role_status(
        self,
        *,
        current_user: CurrentUserContext,
        role_id: str,
        is_active: bool,
    ) -> dict:
        item = self.repo.get_functional_role(role_id)
        if item is None or item.org_id != current_user.org_id:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Functional role not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        if item.code == "unassigned" and not is_active:
            self._raise(
                error_code="VALIDATION_ERROR",
                message="Default functional role cannot be disabled",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        updated = self.repo.update_functional_role_status(role_id=role_id, is_active=is_active)
        if updated is None:
            self._raise(
                error_code="RESOURCE_NOT_FOUND",
                message="Functional role not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        self.repo.create_audit_log(
            org_id=current_user.org_id,
            actor_user_id=current_user.user_id,
            target_type="functional_role",
            target_id=role_id,
            action="ADMIN_UPDATE_FUNCTION_ROLE_STATUS",
            result="SUCCESS",
            metadata={"isActive": is_active},
        )
        return {
            "id": updated.id,
            "orgId": updated.org_id,
            "code": updated.code,
            "name": updated.name,
            "description": updated.description,
            "isActive": updated.is_active,
            "sortOrder": updated.sort_order,
            "createdAt": updated.created_at.isoformat() if updated.created_at else "",
            "updatedAt": updated.updated_at.isoformat() if updated.updated_at else "",
        }
