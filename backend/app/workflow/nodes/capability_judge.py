from __future__ import annotations

from app.model_client.base import ModelClient
from app.schemas import CapabilityJudgementSchema
from app.workflow.state import PreReviewState


class CapabilityJudgeNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        evidence_pack = state.get("evidence_pack", [])
        uncertain_points = state.get("parsed_requirement", {}).get("uncertain_points", [])

        judgement = self.model_client.structured_invoke(
            prompt_name="capability_judge",
            input_data={"uncertain_points": uncertain_points, "evidence_pack": evidence_pack},
            schema=CapabilityJudgementSchema,
        )

        high_quality_count = sum(
            1
            for item in evidence_pack
            if str(item.get("trust_level", "")).upper() == "HIGH" and float(item.get("relevance_score", 0.0)) >= 0.75
        )
        if judgement["status"] == "SUPPORTED" and high_quality_count < 1:
            judgement["status"] = "PARTIALLY_SUPPORTED" if evidence_pack else "NOT_SUPPORTED"
            judgement["reason"] = "高质量证据不足，降级为保守结论。"
            judgement["confidence"] = "low"

        return {
            "capability_judgement": {
                **judgement,
                "evidence_refs": [item.get("chunk_id", "") for item in evidence_pack if item.get("chunk_id")],
            }
        }
