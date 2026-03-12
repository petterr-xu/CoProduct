from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.permissions import require_admin_permission
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository
from app.services import AdminServiceError, AdminUserService

router = APIRouter(prefix="/admin/functional-roles", tags=["admin-functional-roles"])


def _build_service(db: Session) -> AdminUserService:
    from app.core.config import get_settings

    settings = get_settings()
    return AdminUserService(repo=UserRepository(db), api_key_pepper=settings.api_key_pepper)


def _to_http_error(exc: AdminServiceError) -> HTTPException:
    return HTTPException(status_code=exc.http_status, detail={"error_code": exc.error_code, "message": exc.message})


class CreateFunctionalRoleRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class UpdateFunctionalRoleStatusRequest(BaseModel):
    isActive: bool


@router.get("")
def list_functional_roles(
    isActive: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        return service.list_functional_roles(
            current_user=current_user,
            is_active=isActive,
            page=page,
            page_size=pageSize,
        )
    except AdminServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("", status_code=status.HTTP_201_CREATED)
def create_functional_role(
    payload: CreateFunctionalRoleRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        data = service.create_functional_role(
            current_user=current_user,
            code=payload.code,
            name=payload.name,
            description=payload.description,
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
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Create functional role failed"},
        ) from exc


@router.patch("/{role_id}/status")
def update_functional_role_status(
    role_id: str,
    payload: UpdateFunctionalRoleStatusRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        data = service.update_functional_role_status(
            current_user=current_user,
            role_id=role_id,
            is_active=payload.isActive,
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
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Update functional role status failed"},
        ) from exc
