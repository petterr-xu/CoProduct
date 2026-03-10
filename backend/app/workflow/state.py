from __future__ import annotations

from typing import TypedDict


class PreReviewState(TypedDict):
    session_id: str
    parent_session_id: str | None
    request_id: str
    version: int
    normalized_request: dict
    parsed_requirement: dict
    retrieval_plan: dict
    retrieved_candidates: list
    evidence_pack: list
    capability_judgement: dict
    missing_info_items: list
    risk_items: list
    impact_items: list
    report: dict
    status: str
    error_message: str | None

