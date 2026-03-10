from __future__ import annotations

from app.repositories import PreReviewRepository


class SessionService:
    def __init__(self, repo: PreReviewRepository) -> None:
        self.repo = repo

    def create_session(self, request_id: str, parent_session_id: str | None = None) -> tuple[str, int]:
        version = 1
        if parent_session_id:
            parent = self.repo.get_session(parent_session_id)
            if parent is None:
                raise ValueError("parent session not found")
            version = parent.version + 1

        session = self.repo.create_session(
            request_id=request_id,
            parent_session_id=parent_session_id,
            version=version,
            status="PROCESSING",
        )
        return session.id, version

