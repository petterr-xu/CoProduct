from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUserContext:
    """Authenticated user context injected into service layer."""

    user_id: str
    org_id: str
    role: str
    email: str
    display_name: str
    status: str
    session_id: str | None = None
    auth_mode: str = "jwt"

    @property
    def can_write(self) -> bool:
        return self.role in {"OWNER", "ADMIN", "MEMBER"}

    @property
    def is_admin(self) -> bool:
        return self.role in {"OWNER", "ADMIN"}

