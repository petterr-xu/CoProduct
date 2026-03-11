from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import verify_api_token
from app.core.db import get_db
from app.repositories import PreReviewRepository
from app.services import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", dependencies=[Depends(verify_api_token)])
def get_history(
    keyword: str | None = Query(default=None),
    capabilityStatus: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED", "NEED_MORE_INFO"] | None = Query(
        default=None
    ),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """Return paginated history list filtered by keyword and capability status."""
    service = HistoryService(PreReviewRepository(db))
    return service.list_history(
        keyword=keyword,
        capability_status=capabilityStatus,
        page=page,
        page_size=pageSize,
    )
