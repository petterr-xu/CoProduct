class HistoryService:
    """History query service.

    M1/M1.5 keeps this as a placeholder to preserve endpoint contract.
    M3 will replace this with repository-backed pagination/filtering.
    """

    def list_history(self, *, keyword: str | None, capability_status: str | None, page: int, page_size: int) -> dict:
        """Return empty paginated result while history persistence is not implemented."""
        return {"total": 0, "page": page, "pageSize": page_size, "items": []}
