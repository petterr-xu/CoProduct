from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class RequestModel(Base):
    __tablename__ = "requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("req"))
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    background_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    module_hint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("ses"))
    request_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROCESSING")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("rep"))
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    capability_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NEED_MORE_INFO")
    report_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class EvidenceItemModel(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("evi"))
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doc_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    chunk_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    doc_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="product_doc")
    trust_level: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM")


class UploadedFileModel(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("file"))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False, default="application/octet-stream")
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
