from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.db import Base
from app.repositories.prereview_repository import PreReviewRepository
from app.services.attachment_service import AttachmentService
from app.services.history_service import HistoryService
from app.workflow.nodes.impact_analyzer import ImpactAnalyzerNode
from app.workflow.nodes.input_normalizer import InputNormalizerNode
from app.workflow.nodes.risk_analyzer import RiskAnalyzerNode


def _build_repo():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def test_history_service_returns_real_items_with_filter() -> None:
    SessionLocal = _build_repo()
    with SessionLocal() as db:
        repo = PreReviewRepository(db)
        history = HistoryService(repo)

        req_a = repo.create_request("支持导出报名记录", None, None, None)
        ses_a = repo.create_session(request_id=req_a.id, parent_session_id=None, version=1, status="DONE")
        repo.upsert_report(
            session_id=ses_a.id,
            summary="a",
            capability_status="SUPPORTED",
            report_json={"summary": "a"},
        )

        req_b = repo.create_request("活动审批流程", None, None, None)
        ses_b = repo.create_session(request_id=req_b.id, parent_session_id=None, version=1, status="DONE")
        repo.upsert_report(
            session_id=ses_b.id,
            summary="b",
            capability_status="NOT_SUPPORTED",
            report_json={"summary": "b"},
        )
        db.commit()

        full = history.list_history(keyword=None, capability_status=None, page=1, page_size=20)
        filtered = history.list_history(
            keyword="导出",
            capability_status="SUPPORTED",
            page=1,
            page_size=20,
        )

    assert full["total"] == 2
    assert len(full["items"]) == 2
    assert filtered["total"] == 1
    assert filtered["items"][0]["requestText"] == "支持导出报名记录"
    assert filtered["items"][0]["capabilityStatus"] == "SUPPORTED"


def test_attachment_service_updates_parse_status_and_merges_into_normalizer(tmp_path: Path) -> None:
    SessionLocal = _build_repo()
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings(upload_dir=str(upload_dir), max_text_length=200, normalized_text_limit=300)

    with SessionLocal() as db:
        repo = PreReviewRepository(db)
        attachment = AttachmentService(settings=settings, repo=repo)

        file_path = upload_dir / "sample.txt"
        file_path.write_text("这是附件内容", encoding="utf-8")
        file_record = repo.create_uploaded_file(
            file_name="sample.txt",
            file_size=file_path.stat().st_size,
            mime_type="text/plain",
            storage_key=str(file_path),
            parse_status="PENDING",
        )

        merged = attachment.merge_attachment_text([{"file_id": file_record.id}])
        db.commit()

        saved = repo.get_uploaded_file(file_record.id)
        assert saved is not None
        assert saved.parse_status == "DONE"

    node = InputNormalizerNode(settings)
    output = node(
        {
            "normalized_request": {
                "requirement_text": "需要支持导出",
                "background_text": "",
                "additional_context": "",
                "attachments": [{"file_id": file_record.id}],
                "attachment_text": merged,
            }
        }
    )
    assert "附件信息" in output["normalized_request"]["merged_text"]
    assert "这是附件内容" in output["normalized_request"]["merged_text"]


class _FailingClient:
    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type):  # noqa: ANN001
        raise RuntimeError(f"{prompt_name} failed")


def test_risk_and_impact_node_degrade_without_crashing() -> None:
    node_risk = RiskAnalyzerNode(_FailingClient())
    node_impact = ImpactAnalyzerNode(_FailingClient())

    state = {
        "session_id": "ses_1",
        "normalized_request": {"merged_text": "x", "module_hint": "order"},
        "parsed_requirement": {},
    }

    risk = node_risk(state)
    impact = node_impact(state)

    assert risk["risk_items"] == []
    assert impact["impact_items"] == []
