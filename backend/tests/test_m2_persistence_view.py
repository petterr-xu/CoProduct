from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.repositories.prereview_repository import PreReviewRepository
from app.services.persistence_service import PersistenceService


def test_session_result_returns_m2_view_model_shape() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        repo = PreReviewRepository(db)
        persistence = PersistenceService(repo)

        request = repo.create_request(
            requirement_text="支持导出",
            background_text=None,
            business_domain="活动运营",
            module_hint="export_service",
        )
        session = repo.create_session(request_id=request.id, parent_session_id=None, version=1, status="PROCESSING")

        state = {
            "session_id": session.id,
            "report": {
                "summary": "summary text",
                "capabilityJudgement": {
                    "status": "PARTIALLY_SUPPORTED",
                    "reason": "reason text",
                    "confidence": "medium",
                    "evidence_refs": ["chunk_1"],
                },
                "structuredDraft": {
                    "goal": "导出",
                    "actors": ["运营"],
                    "business_objects": ["导出任务"],
                    "data_objects": ["报名记录"],
                    "constraints": ["角色权限边界"],
                    "expected_output": "导出文件",
                    "uncertain_points": [],
                },
                "evidence": [
                    {
                        "doc_id": "doc_1",
                        "doc_title": "导出 API",
                        "chunk_id": "chunk_1",
                        "snippet": "支持导出",
                        "source_type": "api_doc",
                        "relevance_score": 0.9,
                        "trust_level": "HIGH",
                    }
                ],
                "missingInfoItems": [],
                "riskItems": [],
                "impactItems": [],
                "nextSteps": ["补充细节"],
            },
            "capability_judgement": {"status": "PARTIALLY_SUPPORTED"},
            "evidence_pack": [
                {
                    "doc_id": "doc_1",
                    "doc_title": "导出 API",
                    "chunk_id": "chunk_1",
                    "snippet": "支持导出",
                    "source_type": "api_doc",
                    "relevance_score": 0.9,
                    "trust_level": "HIGH",
                }
            ],
            "status": "DONE",
        }

        persistence.persist_workflow_result(state)
        db.commit()

        view = persistence.get_session_result(session.id)

    assert view is not None
    assert view["status"] == "DONE"
    assert view["capability"]["confidence"] == "medium"
    assert "structuredRequirement" in view
    assert "nextActions" in view
    assert "uncertainties" in view

