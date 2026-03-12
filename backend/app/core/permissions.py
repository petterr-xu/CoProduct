from __future__ import annotations

from fastapi import HTTPException, status

from app.core.user_context import CurrentUserContext


def _deny(message: str = "Permission denied") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"error_code": "PERMISSION_DENIED", "message": message},
    )


def require_role(user: CurrentUserContext, allowed_roles: set[str], *, message: str = "Permission denied") -> None:
    if user.role not in allowed_roles:
        raise _deny(message)


def require_write_permission(user: CurrentUserContext) -> None:
    require_role(user, {"OWNER", "ADMIN", "MEMBER"}, message="Write permission required")


def require_admin_permission(user: CurrentUserContext) -> None:
    require_role(user, {"OWNER", "ADMIN"}, message="Admin permission required")
