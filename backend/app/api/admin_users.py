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

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _build_service(db: Session) -> AdminUserService:
    from app.core.config import get_settings

    settings = get_settings()
    return AdminUserService(repo=UserRepository(db), api_key_pepper=settings.api_key_pepper)


def _to_http_error(exc: AdminServiceError) -> HTTPException:
    return HTTPException(status_code=exc.http_status, detail={"error_code": exc.error_code, "message": exc.message})


class CreateUserRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    displayName: str = Field(min_length=1, max_length=255)
    role: str
    orgId: str | None = None


class UpdateUserStatusRequest(BaseModel):
    status: str


class UpdateUserRoleRequest(BaseModel):
    role: str


@router.get("")
def list_users(
    query: str | None = Query(default=None),
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        return service.list_users(
            current_user=current_user,
            query=query,
            role=role,
            user_status=status,
            page=page,
            page_size=pageSize,
        )
    except AdminServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("", status_code=201)
def create_user(
    payload: CreateUserRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        data = service.create_user(
            current_user=current_user,
            email=payload.email,
            display_name=payload.displayName,
            role=payload.role,
            org_id=payload.orgId,
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
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Create user failed"},
        ) from exc


@router.patch("/{user_id}/status")
def update_user_status(
    user_id: str,
    payload: UpdateUserStatusRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        data = service.update_user_status(current_user=current_user, user_id=user_id, next_status=payload.status)
        db.commit()
        return data
    except AdminServiceError as exc:
        db.rollback()
        raise _to_http_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Update user status failed"},
        ) from exc


@router.patch("/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: UpdateUserRoleRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        data = service.update_user_role(current_user=current_user, user_id=user_id, role=payload.role)
        db.commit()
        return data
    except AdminServiceError as exc:
        db.rollback()
        raise _to_http_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Update user role failed"},
        ) from exc
