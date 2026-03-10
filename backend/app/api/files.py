from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.auth import verify_api_token

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", dependencies=[Depends(verify_api_token)])
async def upload_file(file: UploadFile) -> dict:
    # M1 only reserves API surface. File pipeline lands in M3.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error_code": "FILE_UPLOAD_ERROR",
            "message": f"file upload not implemented in M1: {file.filename}",
        },
    )

