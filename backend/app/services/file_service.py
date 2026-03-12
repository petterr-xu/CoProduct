from __future__ import annotations

"""File upload service for local storage and metadata persistence."""

from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository


class FileService:
    """Validate file input, save bytes, and register a reusable file reference."""

    allowed_extensions = {".txt", ".md", ".pdf", ".docx"}

    def __init__(self, settings: Settings, repo: PreReviewRepository) -> None:
        self.settings = settings
        self.repo = repo

    def save_uploaded_file(
        self,
        *,
        file_name: str,
        content_type: str,
        content: bytes,
        current_user: CurrentUserContext | None = None,
    ) -> dict:
        """Persist file content and return frontend-facing UploadedFileRef fields."""
        extension = Path(file_name).suffix.lower()
        if extension not in self.allowed_extensions:
            raise ValueError("FILE_UPLOAD_ERROR: unsupported file type")

        max_bytes = self.settings.upload_max_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise ValueError("FILE_UPLOAD_ERROR: file too large")

        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_id = f"file_{uuid4().hex[:12]}"
        storage_key = str(upload_dir / f"{file_id}{extension}")
        Path(storage_key).write_bytes(content)

        file_record = self.repo.create_uploaded_file(
            file_name=file_name,
            file_size=len(content),
            mime_type=content_type or "application/octet-stream",
            storage_key=storage_key,
            parse_status="PENDING",
            org_id=current_user.org_id if current_user else None,
            created_by_user_id=current_user.user_id if current_user else None,
        )

        return {
            "fileId": file_record.id,
            "fileName": file_record.file_name,
            "fileSize": file_record.file_size,
            "parseStatus": file_record.parse_status,
        }
