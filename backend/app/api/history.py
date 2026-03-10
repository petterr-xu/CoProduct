from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.auth import verify_api_token
from app.services import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", dependencies=[Depends(verify_api_token)])
def get_history(
    keyword: str | None = Query(default=None),
    capabilityStatus: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
) -> dict:
    service = HistoryService()
    return service.list_history(
        keyword=keyword,
        capability_status=capabilityStatus,
        page=page,
        page_size=pageSize,
    )

