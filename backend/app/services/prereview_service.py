from __future__ import annotations

"""Orchestration-facing service for pre-review use cases.

This layer coordinates repository access, workflow invocation, and persistence.
API handlers should call this service instead of touching workflow/repo directly.
"""

from dataclasses import dataclass, field
from uuid import uuid4

from app.core.config import Settings
from app.core.logging import log_event
from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository
from app.services.attachment_service import AttachmentService
from app.services.persistence_service import PersistenceService
from app.services.session_service import SessionService
from app.services.workflow_runner import WorkflowTaskEnvelope
from app.workflow import PreReviewState, PreReviewWorkflow


@dataclass
class PreReviewCreateInput:
    """Input contract for creating a new pre-review session."""

    requirement_text: str
    background_text: str | None = None
    business_domain: str | None = None
    module_hint: str | None = None
    attachments: list[dict] = field(default_factory=list)
    current_user: CurrentUserContext | None = None


@dataclass
class PreReviewRegenerateInput:
    """Input contract for regenerating from an existing session."""

    parent_session_id: str
    additional_context: str | None = None
    attachments: list[dict] = field(default_factory=list)
    current_user: CurrentUserContext | None = None


@dataclass
class PreReviewSubmission:
    """Submission result returned before async queue acceptance."""

    session_id: str
    status: str
    task: WorkflowTaskEnvelope

    def to_response(self) -> dict:
        return {"sessionId": self.session_id, "status": self.status}


class PreReviewService:
    """Application service for create/query/regenerate pre-review flows."""

    def __init__(self, settings: Settings, repo: PreReviewRepository, workflow: PreReviewWorkflow | None = None) -> None:
        self.settings = settings
        self.repo = repo
        self.session_service = SessionService(repo)
        self.persistence_service = PersistenceService(repo)
        self.attachment_service = AttachmentService(settings=settings, repo=repo)
        # Keep workflow injection for compatibility with existing callers/tests.
        # Phase 1.5 submission path no longer invokes workflow in request thread.
        self.workflow = workflow

    def create_prereview(self, payload: PreReviewCreateInput) -> PreReviewSubmission:
        """Create request/session and build async workflow task."""
        request = self.repo.create_request(
            requirement_text=payload.requirement_text,
            background_text=payload.background_text,
            business_domain=payload.business_domain,
            module_hint=payload.module_hint,
            org_id=payload.current_user.org_id if payload.current_user else None,
            created_by_user_id=payload.current_user.user_id if payload.current_user else None,
        )
        session_id, version = self.session_service.create_session(request.id, current_user=payload.current_user)
        attachment_text = self.attachment_service.merge_attachment_text(
            payload.attachments,
            current_user=payload.current_user,
        )

        initial_state: PreReviewState = {
            "session_id": session_id,
            "parent_session_id": None,
            "request_id": request.id,
            "version": version,
            "normalized_request": self._build_normalized_request(
                requirement_text=payload.requirement_text,
                background_text=payload.background_text or "",
                business_domain=payload.business_domain,
                module_hint=payload.module_hint,
                attachments=payload.attachments,
                additional_context="",
                attachment_text=attachment_text,
            ),
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

        task = self._build_task(
            task_type="CREATE",
            session_id=session_id,
            request_id=request.id,
            parent_session_id=None,
            version=version,
            current_user=payload.current_user,
            initial_state=initial_state,
        )
        self.repo.upsert_workflow_job(
            session_id=session_id,
            task_type=task.task_type,
            payload=task.to_payload(),
            status="QUEUED",
            org_id=payload.current_user.org_id if payload.current_user else None,
            created_by_user_id=payload.current_user.user_id if payload.current_user else None,
        )
        log_event("workflow_submission_accepted", request_id=request.id, session_id=session_id, status="PROCESSING")
        return PreReviewSubmission(session_id=session_id, status="PROCESSING", task=task)

    def regenerate_prereview(self, payload: PreReviewRegenerateInput) -> PreReviewSubmission:
        """Create child session and build async workflow task."""
        parent_session = self.repo.get_session(payload.parent_session_id, scope=payload.current_user)
        if parent_session is None:
            raise ValueError("parent session not found")

        request = self.repo.get_request(parent_session.request_id, scope=payload.current_user)
        if request is None:
            raise ValueError("request not found")

        session_id, version = self.session_service.create_session(
            request_id=request.id,
            current_user=payload.current_user,
            parent_session_id=parent_session.id,
        )
        attachment_text = self.attachment_service.merge_attachment_text(
            payload.attachments,
            current_user=payload.current_user,
        )

        initial_state: PreReviewState = {
            "session_id": session_id,
            "parent_session_id": parent_session.id,
            "request_id": request.id,
            "version": version,
            "normalized_request": self._build_normalized_request(
                requirement_text=request.requirement_text,
                background_text=request.background_text or "",
                business_domain=request.business_domain,
                module_hint=request.module_hint,
                attachments=payload.attachments,
                additional_context=payload.additional_context or "",
                attachment_text=attachment_text,
            ),
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

        task = self._build_task(
            task_type="REGENERATE",
            session_id=session_id,
            request_id=request.id,
            parent_session_id=parent_session.id,
            version=version,
            current_user=payload.current_user,
            initial_state=initial_state,
        )
        self.repo.upsert_workflow_job(
            session_id=session_id,
            task_type=task.task_type,
            payload=task.to_payload(),
            status="QUEUED",
            org_id=payload.current_user.org_id if payload.current_user else None,
            created_by_user_id=payload.current_user.user_id if payload.current_user else None,
        )
        log_event(
            "workflow_regenerate_submission_accepted",
            request_id=request.id,
            session_id=session_id,
            parent_session_id=parent_session.id,
            status="PROCESSING",
        )
        return PreReviewSubmission(session_id=session_id, status="PROCESSING", task=task)

    def get_prereview(self, session_id: str, current_user: CurrentUserContext | None = None) -> dict | None:
        """Return frontend-facing view model for a session."""
        return self.persistence_service.get_session_result(session_id, current_user=current_user)

    @staticmethod
    def _build_normalized_request(
        *,
        requirement_text: str,
        background_text: str,
        business_domain: str | None,
        module_hint: str | None,
        attachments: list[dict],
        additional_context: str,
        attachment_text: str,
    ) -> dict:
        return {
            "requirement_text": requirement_text,
            "background_text": background_text,
            "business_domain": business_domain,
            "module_hint": module_hint,
            "attachments": attachments,
            "additional_context": additional_context,
            "attachment_text": attachment_text,
        }

    @staticmethod
    def _build_task(
        *,
        task_type: str,
        session_id: str,
        request_id: str,
        parent_session_id: str | None,
        version: int,
        current_user: CurrentUserContext | None,
        initial_state: PreReviewState,
    ) -> WorkflowTaskEnvelope:
        return WorkflowTaskEnvelope(
            task_type=task_type,
            session_id=session_id,
            request_id=request_id,
            parent_session_id=parent_session_id,
            version=version,
            org_id=current_user.org_id if current_user else None,
            actor_user_id=current_user.user_id if current_user else None,
            trace_id=f"trace_{uuid4().hex[:12]}",
            initial_state=initial_state,
        )
