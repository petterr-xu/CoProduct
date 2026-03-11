from __future__ import annotations

from app.repositories import PreReviewRepository


class HistoryService:
    """Read-model service for pre-review history list."""

    def __init__(self, repo: PreReviewRepository) -> None:
        self.repo = repo

    def list_history(self, *, keyword: str | None, capability_status: str | None, page: int, page_size: int) -> dict:
        """Return paginated history items filtered by keyword and capability status."""
        total, items = self.repo.list_history(
            keyword=keyword,
            capability_status=capability_status,
            page=page,
            page_size=page_size,
        )
        return {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "items": items,
        }
