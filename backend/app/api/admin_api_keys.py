from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.permissions import require_admin_permission
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository
from app.services import AdminServiceError, AdminUserService

router = APIRouter(prefix="/admin/api-keys", tags=["admin-api-keys"])


def _build_service(db: Session) -> AdminUserService:
    from app.core.config import get_settings

    settings = get_settings()
    return AdminUserService(repo=UserRepository(db), api_key_pepper=settings.api_key_pepper)


def _to_http_error(exc: AdminServiceError) -> HTTPException:
    return HTTPException(status_code=exc.http_status, detail={"error_code": exc.error_code, "message": exc.message})


class IssueApiKeyRequest(BaseModel):
    userId: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=255)
    expiresAt: datetime | None = None


@router.get("")
def list_api_keys(
    userId: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        return service.list_api_keys(
            current_user=current_user,
            user_id=userId,
            key_status=status,
            page=page,
            page_size=pageSize,
        )
    except AdminServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("", status_code=status.HTTP_201_CREATED)
def issue_api_key(
    payload: IssueApiKeyRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        result = service.issue_api_key(
            current_user=current_user,
            user_id=payload.userId,
            name=payload.name,
            expires_at=payload.expiresAt,
        )
        db.commit()
        return {
            "keyId": result.key_id,
            "keyPrefix": result.key_prefix,
            "plainTextKey": result.plain_text_key,
            "expiresAt": result.expires_at,
        }
    except AdminServiceError as exc:
        db.rollback()
        raise _to_http_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Issue API key failed"},
        ) from exc


@router.post("/{key_id}/revoke")
def revoke_api_key(
    key_id: str,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin_permission(current_user)
    service = _build_service(db)
    try:
        result = service.revoke_api_key(current_user=current_user, key_id=key_id)
        db.commit()
        return result
    except AdminServiceError as exc:
        db.rollback()
        raise _to_http_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PERSISTENCE_ERROR", "message": "Revoke API key failed"},
        ) from exc
