from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.permissions import require_admin_permission
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository
from app.services import AdminServiceError, AdminUserService

router = APIRouter(prefix="/admin/members", tags=["admin-members"])


def _build_service(db: Session) -> AdminUserService:
    from app.core.config import get_settings

    settings = get_settings()
    return AdminUserService(repo=UserRepository(db), api_key_pepper=settings.api_key_pepper)


def _to_http_error(exc: AdminServiceError) -> HTTPException:
    return HTTPException(status_code=exc.http_status, detail={"error_code": exc.error_code, "message": exc.message})


class UpdateMemberRoleRequest(BaseModel):
    role: str
    reason: str | None = Field(default=None, max_length=500)


class UpdateMemberStatusRequest(BaseModel):
    status: str
    reason: str | None = Field(default=None, max_length=500)


class UpdateMemberFunctionalRoleRequest(BaseModel):
    functionalRoleId: str = Field(min_length=1)
    reason: str | None = Field(default=None, max_length=500)


@router.get("")
def list_members(
    query: str | None = Query(default=None),
    permissionRole: str | None = Query(default=None),
    memberStatus: str | None = Query(default=None),
    functionalRoleId: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        return service.list_members(
            current_user=current_user,
            query=query,
            permission_role=permissionRole,
            member_status=memberStatus,
            functional_role_id=functionalRoleId,
            page=page,
            page_size=pageSize,
        )
    except AdminServiceError as exc:
        raise _to_http_error(exc) from exc


@router.patch("/{member_id}/role")
def update_member_role(
    member_id: str,
    payload: UpdateMemberRoleRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        data = service.update_member_role(
            current_user=current_user,
            membership_id=member_id,
            role=payload.role,
            reason=payload.reason,
        )
        db.commit()
        return data
    except AdminServiceError as exc:
        db.rollback()
        raise _to_http_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Update member role failed"},
        ) from exc


@router.patch("/{member_id}/status")
def update_member_status(
    member_id: str,
    payload: UpdateMemberStatusRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        data = service.update_member_status(
            current_user=current_user,
            membership_id=member_id,
            member_status=payload.status,
            reason=payload.reason,
        )
        db.commit()
        return data
    except AdminServiceError as exc:
        db.rollback()
        raise _to_http_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Update member status failed"},
        ) from exc


@router.patch("/{member_id}/functional-role")
def update_member_functional_role(
    member_id: str,
    payload: UpdateMemberFunctionalRoleRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        data = service.update_member_functional_role(
            current_user=current_user,
            membership_id=member_id,
            functional_role_id=payload.functionalRoleId,
            reason=payload.reason,
        )
        db.commit()
        return data
    except AdminServiceError as exc:
        db.rollback()
        raise _to_http_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Update member functional role failed"},
        ) from exc
