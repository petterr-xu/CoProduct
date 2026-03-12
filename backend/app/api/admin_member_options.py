from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.permissions import require_admin_permission
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository
from app.services import AdminServiceError, AdminUserService

router = APIRouter(prefix="/admin/member-options", tags=["admin-member-options"])


def _build_service(db: Session) -> AdminUserService:
    from app.core.config import get_settings

    settings = get_settings()
    return AdminUserService(repo=UserRepository(db), api_key_pepper=settings.api_key_pepper)


def _to_http_error(exc: AdminServiceError) -> HTTPException:
    return HTTPException(status_code=exc.http_status, detail={"error_code": exc.error_code, "message": exc.message})


class MemberOptionItem(BaseModel):
    userId: str
    membershipId: str
    email: str
    displayName: str
    permissionRole: str
    memberStatus: str
    orgId: str


class MemberOptionsResponse(BaseModel):
    items: list[MemberOptionItem]


@router.get("", response_model=MemberOptionsResponse)
def list_member_options(
    query: str = Query(min_length=2),
    orgId: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        return service.list_member_options(
            current_user=current_user,
            query=query,
            org_id=orgId,
            limit=limit,
        )
    except AdminServiceError as exc:
        raise _to_http_error(exc) from exc
