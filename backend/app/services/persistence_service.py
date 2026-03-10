from __future__ import annotations

import json

from app.repositories import PreReviewRepository
from app.workflow.state import PreReviewState


class PersistenceService:
    def __init__(self, repo: PreReviewRepository) -> None:
        self.repo = repo

    def persist_workflow_result(self, state: PreReviewState) -> None:
        report = state.get("report", {})
        capability = state.get("capability_judgement", {})
        self.repo.upsert_report(
            session_id=state["session_id"],
            summary=report.get("summary", ""),
            capability_status=capability.get("status", "NEED_MORE_INFO"),
            report_json=report,
        )
        self.repo.replace_evidence_items(state["session_id"], state.get("evidence_pack", []))
        self.repo.update_session_status(session_id=state["session_id"], status=state.get("status", "SUCCESS"))

    def persist_workflow_failure(self, session_id: str, error_message: str) -> None:
        self.repo.update_session_status(session_id=session_id, status="FAILED", error_message=error_message)

    def get_session_result(self, session_id: str) -> dict | None:
        session = self.repo.get_session(session_id)
        if session is None:
            return None

        report = self.repo.get_report(session_id)
        evidence_items = self.repo.list_evidence(session_id)

        report_payload = {}
        if report is not None:
            report_payload = json.loads(report.report_json)

        return {
            "sessionId": session.id,
            "parentSessionId": session.parent_session_id,
            "version": session.version,
            "status": session.status,
            "report": report_payload,
            "evidenceCount": len(evidence_items),
            "errorCode": "WORKFLOW_ERROR" if session.status == "FAILED" else None,
            "errorMessage": session.error_message,
        }

