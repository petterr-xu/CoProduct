from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import verify_api_token
from app.core.config import get_settings
from app.core.db import get_db
from app.repositories import PreReviewRepository
from app.services import FileService

router = APIRouter(prefix="/files", tags=["files"])
settings = get_settings()


@router.post("/upload", dependencies=[Depends(verify_api_token)])
async def upload_file(file: UploadFile, db: Session = Depends(get_db)) -> dict:
    """Upload a file, persist metadata, and return a stable fileId reference."""
    repo = PreReviewRepository(db)
    service = FileService(settings=settings, repo=repo)
    try:
        content = await file.read()
        result = service.save_uploaded_file(
            file_name=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "FILE_UPLOAD_ERROR", "message": str(exc)},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "FILE_UPLOAD_ERROR", "message": "file upload failed"},
        ) from exc
