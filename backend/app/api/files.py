from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.core.permissions import require_write_permission
from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository
from app.services import FileService

router = APIRouter(prefix="/files", tags=["files"])
settings = get_settings()


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Upload a file, persist metadata, and return a stable fileId reference."""
    require_write_permission(current_user)
    repo = PreReviewRepository(db)
    service = FileService(settings=settings, repo=repo)
    try:
        content = await file.read()
        result = service.save_uploaded_file(
            file_name=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            content=content,
            current_user=current_user,
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raw_message = str(exc)
        error_code = "FILE_UPLOAD_ERROR"
        message = raw_message
        if ":" in raw_message:
            prefix, suffix = raw_message.split(":", 1)
            prefix = prefix.strip()
            if prefix in {"FILE_UPLOAD_ERROR", "FILE_PARSE_ERROR"}:
                error_code = prefix
                message = suffix.strip() or raw_message
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": error_code, "message": message},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "FILE_UPLOAD_ERROR", "message": "file upload failed"},
        ) from exc
