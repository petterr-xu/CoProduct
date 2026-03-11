from __future__ import annotations

"""Persistence boundary for workflow results and frontend view mapping."""

import json

from app.repositories import PreReviewRepository
from app.workflow.state import PreReviewState


class PersistenceService:
    """Store workflow outputs and expose normalized read models."""

    def __init__(self, repo: PreReviewRepository) -> None:
        self.repo = repo

    def persist_workflow_result(self, state: PreReviewState) -> None:
        """Persist report/evidence/session status for a successful workflow run."""
        report = state.get("report", {})
        capability = state.get("capability_judgement", {})
        self.repo.upsert_report(
            session_id=state["session_id"],
            summary=report.get("summary", ""),
            capability_status=capability.get("status", "NEED_MORE_INFO"),
            report_json=report,
        )
        self.repo.replace_evidence_items(state["session_id"], state.get("evidence_pack", []))
        self.repo.update_session_status(session_id=state["session_id"], status=state.get("status", "DONE"))

    def persist_workflow_failure(self, session_id: str, error_message: str) -> None:
        """Persist failure status and error message for troubleshooting."""
        self.repo.update_session_status(session_id=session_id, status="FAILED", error_message=error_message)

    def get_session_result(self, session_id: str) -> dict | None:
        """Build frontend-aligned response shape from stored session/report/evidence."""
        session = self.repo.get_session(session_id)
        if session is None:
            return None

        report = self.repo.get_report(session_id)
        evidence_items = self.repo.list_evidence(session_id)

        report_payload = {}
        if report is not None:
            report_payload = json.loads(report.report_json)

        status = self._to_view_status(session.status)
        capability = report_payload.get("capabilityJudgement", {})
        parsed = report_payload.get("structuredDraft", {})
        evidence = report_payload.get("evidence", [])
        missing_items = report_payload.get("missingInfoItems", [])
        risks = report_payload.get("riskItems", [])
        impacts = report_payload.get("impactItems", [])
        confidence = capability.get("confidence") or self._confidence_from_evidence(evidence)

        return {
            "sessionId": session.id,
            "parentSessionId": session.parent_session_id,
            "version": session.version,
            "status": status,
            "summary": report_payload.get("summary", ""),
            "capability": {
                "status": capability.get("status", "NEED_MORE_INFO"),
                "reason": capability.get("reason", ""),
                "confidence": confidence,
            },
            "evidence": evidence,
            "structuredRequirement": {
                "goal": parsed.get("goal", ""),
                "actors": parsed.get("actors", []),
                "scope": parsed.get("business_objects", []),
                "constraints": parsed.get("constraints", []),
                "expectedOutput": parsed.get("expected_output", ""),
            },
            "missingInfo": [item.get("question", "") for item in missing_items if item.get("question")],
            "risks": [
                {
                    "title": item.get("type", "risk"),
                    "description": item.get("description", ""),
                    "level": str(item.get("level", "medium")).lower(),
                }
                for item in risks
            ],
            "impactScope": [
                f'{item.get("module", "")}: {item.get("reason", "")}'.strip(": ")
                for item in impacts
                if item.get("module")
            ],
            "nextActions": report_payload.get("nextSteps", []),
            "uncertainties": parsed.get("uncertain_points", []),
            "evidenceCount": len(evidence_items),
            "errorCode": "WORKFLOW_ERROR" if status == "FAILED" else None,
            "errorMessage": session.error_message,
        }

    @staticmethod
    def _to_view_status(raw_status: str) -> str:
        """Map internal/raw status to frontend status enum."""
        if raw_status in {"DONE", "PROCESSING", "FAILED"}:
            return raw_status
        if raw_status == "SUCCESS":
            return "DONE"
        return "FAILED"

    @staticmethod
    def _confidence_from_evidence(evidence: list[dict]) -> str:
        """Infer coarse confidence level from evidence trust distribution."""
        if not evidence:
            return "low"
        high_count = sum(1 for item in evidence if str(item.get("trust_level", "")).upper() == "HIGH")
        if high_count >= 2:
            return "high"
        if high_count >= 1:
            return "medium"
        return "low"
