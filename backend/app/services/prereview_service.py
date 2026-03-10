from __future__ import annotations

"""Orchestration-facing service for pre-review use cases.

This layer coordinates repository access, workflow invocation, and persistence.
API handlers should call this service instead of touching workflow/repo directly.
"""

from dataclasses import dataclass, field

from app.core.config import Settings
from app.core.logging import log_event
from app.repositories import PreReviewRepository
from app.services.persistence_service import PersistenceService
from app.services.session_service import SessionService
from app.workflow import PreReviewState, PreReviewWorkflow


@dataclass
class PreReviewCreateInput:
    """Input contract for creating a new pre-review session."""

    requirement_text: str
    background_text: str | None = None
    business_domain: str | None = None
    module_hint: str | None = None
    attachments: list[dict] = field(default_factory=list)


@dataclass
class PreReviewRegenerateInput:
    """Input contract for regenerating from an existing session."""

    parent_session_id: str
    additional_context: str | None = None
    attachments: list[dict] = field(default_factory=list)


class PreReviewService:
    """Application service for create/query/regenerate pre-review flows."""

    def __init__(self, settings: Settings, repo: PreReviewRepository, workflow: PreReviewWorkflow | None = None) -> None:
        self.settings = settings
        self.repo = repo
        self.session_service = SessionService(repo)
        self.persistence_service = PersistenceService(repo)
        self.workflow = workflow or PreReviewWorkflow(settings)

    def create_prereview(self, payload: PreReviewCreateInput) -> dict:
        """Create request/session, execute workflow, and persist outputs."""
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
                status=final_state.get("status", "DONE"),
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

    def regenerate_prereview(self, payload: PreReviewRegenerateInput) -> dict:
        """Create a child session from parent session and rerun the full workflow."""
        parent_session = self.repo.get_session(payload.parent_session_id)
        if parent_session is None:
            raise ValueError("parent session not found")

        request = self.repo.get_request(parent_session.request_id)
        if request is None:
            raise ValueError("request not found")

        session_id, version = self.session_service.create_session(
            request_id=request.id,
            parent_session_id=parent_session.id,
        )

        initial_state: PreReviewState = {
            "session_id": session_id,
            "parent_session_id": parent_session.id,
            "request_id": request.id,
            "version": version,
            "normalized_request": {
                "requirement_text": request.requirement_text,
                "background_text": request.background_text or "",
                "business_domain": request.business_domain,
                "module_hint": request.module_hint,
                "attachments": payload.attachments,
                "additional_context": payload.additional_context or "",
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
                "workflow_regenerated",
                request_id=request.id,
                session_id=session_id,
                parent_session_id=parent_session.id,
                status=final_state.get("status", "DONE"),
            )
            return {"sessionId": session_id, "status": "PROCESSING"}
        except Exception as exc:  # noqa: BLE001
            self.persistence_service.persist_workflow_failure(session_id, str(exc))
            log_event(
                "workflow_regenerate_failed",
                request_id=request.id,
                session_id=session_id,
                parent_session_id=parent_session.id,
                status="FAILED",
                error_code="WORKFLOW_ERROR",
                error_message=str(exc),
            )
            raise

    def get_prereview(self, session_id: str) -> dict | None:
        """Return frontend-facing view model for a session."""
        return self.persistence_service.get_session_result(session_id)
