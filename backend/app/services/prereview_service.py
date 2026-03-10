from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import Settings
from app.core.logging import log_event
from app.repositories import PreReviewRepository
from app.services.persistence_service import PersistenceService
from app.services.session_service import SessionService
from app.workflow import PreReviewState, PreReviewWorkflow


@dataclass
class PreReviewCreateInput:
    requirement_text: str
    background_text: str | None = None
    business_domain: str | None = None
    module_hint: str | None = None
    attachments: list[dict] = field(default_factory=list)


class PreReviewService:
    def __init__(self, settings: Settings, repo: PreReviewRepository, workflow: PreReviewWorkflow | None = None) -> None:
        self.settings = settings
        self.repo = repo
        self.session_service = SessionService(repo)
        self.persistence_service = PersistenceService(repo)
        self.workflow = workflow or PreReviewWorkflow(settings)

    def create_prereview(self, payload: PreReviewCreateInput) -> dict:
        request = self.repo.create_request(
            requirement_text=payload.requirement_text,
            background_text=payload.background_text,
            business_domain=payload.business_domain,
            module_hint=payload.module_hint,
        )
        session_id, version = self.session_service.create_session(request.id)

        initial_state: PreReviewState = {
            "session_id": session_id,
            "parent_session_id": None,
            "request_id": request.id,
            "version": version,
            "normalized_request": {
                "requirement_text": payload.requirement_text,
                "background_text": payload.background_text or "",
                "business_domain": payload.business_domain,
                "module_hint": payload.module_hint,
                "attachments": payload.attachments,
                "additional_context": "",
            },
            "parsed_requirement": {},
            "retrieval_plan": {},
            "retrieved_candidates": [],
            "evidence_pack": [],
            "capability_judgement": {},
            "missing_info_items": [],
            "risk_items": [],
            "impact_items": [],
            "report": {},
            "status": "PROCESSING",
            "error_message": None,
        }

        try:
            final_state = self.workflow.invoke(initial_state)
            self.persistence_service.persist_workflow_result(final_state)
            log_event(
                "workflow_completed",
                request_id=request.id,
                session_id=session_id,
                status=final_state.get("status", "SUCCESS"),
            )
            return {"sessionId": session_id, "status": "PROCESSING"}
        except Exception as exc:  # noqa: BLE001
            self.persistence_service.persist_workflow_failure(session_id, str(exc))
            log_event(
                "workflow_failed",
                request_id=request.id,
                session_id=session_id,
                status="FAILED",
                error_code="WORKFLOW_ERROR",
                error_message=str(exc),
            )
            raise

    def get_prereview(self, session_id: str) -> dict | None:
        return self.persistence_service.get_session_result(session_id)
