from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.models import EvidenceItemModel, ReportModel, RequestModel, SessionModel, UploadedFileModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PreReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_request(
        self,
        requirement_text: str,
        background_text: str | None,
        business_domain: str | None,
        module_hint: str | None,
    ) -> RequestModel:
        item = RequestModel(
            requirement_text=requirement_text,
            background_text=background_text,
            business_domain=business_domain,
            module_hint=module_hint,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def get_request(self, request_id: str) -> RequestModel | None:
        return self.db.get(RequestModel, request_id)

    def create_session(
        self,
        request_id: str,
        parent_session_id: str | None,
        version: int,
        status: str = "PROCESSING",
    ) -> SessionModel:
        item = SessionModel(
            request_id=request_id,
            parent_session_id=parent_session_id,
            version=version,
            status=status,
            started_at=utc_now(),
        )
        self.db.add(item)
        self.db.flush()
        return item

    def get_session(self, session_id: str) -> SessionModel | None:
        return self.db.get(SessionModel, session_id)

    def get_latest_session_by_request(self, request_id: str) -> SessionModel | None:
        stmt: Select[tuple[SessionModel]] = (
            select(SessionModel)
            .where(SessionModel.request_id == request_id)
            .order_by(desc(SessionModel.version))
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def update_session_status(self, session_id: str, status: str, error_message: str | None = None) -> None:
        session = self.db.get(SessionModel, session_id)
        if session is None:
            return
        session.status = status
        session.error_message = error_message
        session.finished_at = utc_now()
        self.db.add(session)

    def upsert_report(
        self,
        session_id: str,
        summary: str,
        capability_status: str,
        report_json: dict,
    ) -> ReportModel:
        stmt: Select[tuple[ReportModel]] = select(ReportModel).where(ReportModel.session_id == session_id).limit(1)
        existing = self.db.execute(stmt).scalar_one_or_none()
        payload = json.dumps(report_json, ensure_ascii=False)

        if existing is None:
            existing = ReportModel(
                session_id=session_id,
                summary=summary,
                capability_status=capability_status,
                report_json=payload,
            )
        else:
            existing.summary = summary
            existing.capability_status = capability_status
            existing.report_json = payload

        self.db.add(existing)
        self.db.flush()
        return existing

    def replace_evidence_items(self, session_id: str, evidence_pack: list[dict]) -> None:
        self.db.query(EvidenceItemModel).filter(EvidenceItemModel.session_id == session_id).delete()
        for item in evidence_pack:
            model = EvidenceItemModel(
                session_id=session_id,
                doc_id=item.get("doc_id", ""),
                chunk_id=item.get("chunk_id", ""),
                doc_title=item.get("doc_title", ""),
                snippet=item.get("snippet", ""),
                relevance_score=float(item.get("relevance_score", 0.0)),
                source_type=item.get("source_type", "product_doc"),
                trust_level=item.get("trust_level", "MEDIUM"),
            )
            self.db.add(model)
        self.db.flush()

    def get_report(self, session_id: str) -> ReportModel | None:
        stmt: Select[tuple[ReportModel]] = select(ReportModel).where(ReportModel.session_id == session_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_evidence(self, session_id: str) -> list[EvidenceItemModel]:
        stmt: Select[tuple[EvidenceItemModel]] = select(EvidenceItemModel).where(
            EvidenceItemModel.session_id == session_id
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_uploaded_file(
        self,
        file_name: str,
        file_size: int,
        mime_type: str,
        storage_key: str,
        parse_status: str = "PENDING",
    ) -> UploadedFileModel:
        item = UploadedFileModel(
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            storage_key=storage_key,
            parse_status=parse_status,
        )
        self.db.add(item)
        self.db.flush()
        return item
