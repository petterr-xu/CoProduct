from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository
from app.services import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def get_history(
    keyword: str | None = Query(default=None),
    capabilityStatus: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED", "NEED_MORE_INFO"] | None = Query(
        default=None
    ),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return paginated history list filtered by keyword and capability status."""
    service = HistoryService(PreReviewRepository(db))
    return service.list_history(
        keyword=keyword,
        capability_status=capabilityStatus,
        page=page,
        page_size=pageSize,
        current_user=current_user,
    )
