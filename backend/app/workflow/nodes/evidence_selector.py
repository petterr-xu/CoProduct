from __future__ import annotations

from app.workflow.state import PreReviewState


class EvidenceSelectorNode:
    def __call__(self, state: PreReviewState) -> dict:
        candidates = state.get("retrieved_candidates", [])
        sorted_candidates = sorted(candidates, key=lambda item: item.get("relevance_score", 0.0), reverse=True)
        evidence_pack = sorted_candidates[:8]
        return {"evidence_pack": evidence_pack}

