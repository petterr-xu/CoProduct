from __future__ import annotations

"""Session lifecycle service (create and version progression)."""

from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository


class SessionService:
    """Encapsulate session creation rules and version increment logic."""

    def __init__(self, repo: PreReviewRepository) -> None:
        self.repo = repo

    def create_session(
        self,
        request_id: str,
        *,
        current_user: CurrentUserContext | None = None,
        parent_session_id: str | None = None,
    ) -> tuple[str, int]:
        """Create a new session and return (session_id, version)."""
        version = 1
        if parent_session_id:
            parent = self.repo.get_session(parent_session_id, scope=current_user)
            if parent is None:
                raise ValueError("parent session not found")
            version = parent.version + 1

        session = self.repo.create_session(
            request_id=request_id,
            parent_session_id=parent_session_id,
            version=version,
            status="PROCESSING",
            org_id=current_user.org_id if current_user else None,
            created_by_user_id=current_user.user_id if current_user else None,
        )
        return session.id, version
