from __future__ import annotations

from app.model_client.base import ModelClient
from app.schemas import EvidenceItemSchema
from app.workflow.state import PreReviewState


class EvidenceSelectorNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        candidates = state.get("retrieved_candidates", [])
        if not candidates:
            return {"evidence_pack": []}

        query = state.get("normalized_request", {}).get("merged_text", "")
        snippets = [str(item.get("snippet", "")) for item in candidates]
        ranked_indices = self.model_client.rerank(query, snippets)

        ordered = [candidates[index] for index in ranked_indices if 0 <= index < len(candidates)]
        top_eight = ordered[:8]
        evidence_pack = [EvidenceItemSchema.model_validate(item).model_dump() for item in top_eight]
        return {"evidence_pack": evidence_pack}
