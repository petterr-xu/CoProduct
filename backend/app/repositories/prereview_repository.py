from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Select, desc, func, or_, select
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

    def get_uploaded_file(self, file_id: str) -> UploadedFileModel | None:
        return self.db.get(UploadedFileModel, file_id)

    def update_uploaded_file_parse_status(self, file_id: str, parse_status: str) -> UploadedFileModel | None:
        item = self.db.get(UploadedFileModel, file_id)
        if item is None:
            return None
        item.parse_status = parse_status
        self.db.add(item)
        self.db.flush()
        return item

    def list_history(
        self,
        *,
        keyword: str | None,
        capability_status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[int, list[dict]]:
        filters = []
        if keyword:
            pattern = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    RequestModel.requirement_text.ilike(pattern),
                    RequestModel.background_text.ilike(pattern),
                )
            )
        if capability_status:
            filters.append(ReportModel.capability_status == capability_status)

        total_stmt = (
            select(func.count(SessionModel.id))
            .select_from(SessionModel)
            .join(RequestModel, SessionModel.request_id == RequestModel.id)
            .outerjoin(ReportModel, ReportModel.session_id == SessionModel.id)
        )
        if filters:
            total_stmt = total_stmt.where(*filters)
        total = int(self.db.execute(total_stmt).scalar_one() or 0)

        query_stmt = (
            select(
                SessionModel.id.label("session_id"),
                SessionModel.version,
                SessionModel.started_at,
                RequestModel.requirement_text,
                ReportModel.capability_status,
            )
            .select_from(SessionModel)
            .join(RequestModel, SessionModel.request_id == RequestModel.id)
            .outerjoin(ReportModel, ReportModel.session_id == SessionModel.id)
        )
        if filters:
            query_stmt = query_stmt.where(*filters)

        rows = self.db.execute(
            query_stmt
            .order_by(desc(SessionModel.started_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        items = [
            {
                "sessionId": row.session_id,
                "requestText": row.requirement_text,
                "capabilityStatus": row.capability_status or "NEED_MORE_INFO",
                "version": row.version,
                "createdAt": row.started_at.isoformat() if row.started_at else "",
            }
            for row in rows
        ]
        return total, items
