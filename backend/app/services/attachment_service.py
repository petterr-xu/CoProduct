from __future__ import annotations

"""Attachment parsing service used by create/regenerate pre-review flows."""

from pathlib import Path

from app.core.config import Settings
from app.core.logging import log_event
from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository
from app.utils.text import clean_text, truncate_text


class AttachmentService:
    """Resolve attachment file IDs into normalized text snippets."""

    supported_parse_extensions = {".txt", ".md"}

    def __init__(self, settings: Settings, repo: PreReviewRepository) -> None:
        self.settings = settings
        self.repo = repo

    def merge_attachment_text(self, attachments: list[dict], current_user: CurrentUserContext | None = None) -> str:
        """Best-effort parse of attachments; failures are logged and skipped."""
        snippets: list[str] = []
        for attachment in attachments:
            file_id = str(attachment.get("file_id", "")).strip()
            if not file_id:
                continue
            snippet = self._parse_single_attachment(file_id, current_user=current_user)
            if snippet:
                snippets.append(snippet)
        return "\n\n".join(snippets)

    def _parse_single_attachment(self, file_id: str, current_user: CurrentUserContext | None = None) -> str:
        file_record = self.repo.get_uploaded_file(file_id, scope=current_user)
        if file_record is None:
            log_event(
                "attachment_missing",
                file_id=file_id,
                error_code="FILE_PARSE_ERROR",
                error_message="attachment fileId not found",
            )
            return ""

        # Keep state transitions visible for troubleshooting parse pipelines.
        if file_record.parse_status != "DONE":
            self.repo.update_uploaded_file_parse_status(file_id, "PARSING")

        try:
            path = Path(file_record.storage_key)
            content = self._extract_text(path)
            normalized = truncate_text(clean_text(content), self.settings.max_text_length)
            if not normalized:
                raise ValueError("empty parsed text")
            self.repo.update_uploaded_file_parse_status(file_id, "DONE")
            log_event("attachment_parsed", file_id=file_id, file_name=file_record.file_name, parse_status="DONE")
            return f"附件[{file_record.file_name}]：\n{normalized}"
        except Exception as exc:  # noqa: BLE001
            self.repo.update_uploaded_file_parse_status(file_id, "FAILED")
            log_event(
                "attachment_parse_failed",
                file_id=file_id,
                file_name=file_record.file_name,
                error_code="FILE_PARSE_ERROR",
                error_message=str(exc),
            )
            return ""

    def _extract_text(self, file_path: Path) -> str:
        if not file_path.exists():
            raise ValueError("stored file missing")

        extension = file_path.suffix.lower()
        if extension not in self.supported_parse_extensions:
            raise ValueError(f"unsupported parser for extension: {extension}")

        # Decode with replacement to keep workflow resilient to mixed encodings.
        raw = file_path.read_bytes()
        return raw.decode("utf-8", errors="replace")
