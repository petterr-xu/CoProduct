from __future__ import annotations

from app.workflow.state import PreReviewState


class CapabilityJudgeNode:
    def __call__(self, state: PreReviewState) -> dict:
        evidence_pack = state.get("evidence_pack", [])
        uncertain_points = state.get("parsed_requirement", {}).get("uncertain_points", [])

        has_high_quality = any(item.get("trust_level") == "HIGH" for item in evidence_pack)

        if uncertain_points:
            status = "NEED_MORE_INFO"
            reason = "需求关键信息不完整。"
        elif not evidence_pack:
            status = "NOT_SUPPORTED"
            reason = "未检索到有效证据。"
        elif has_high_quality:
            status = "PARTIALLY_SUPPORTED"
            reason = "存在可复用能力，但仍需补全约束信息。"
        else:
            status = "NOT_SUPPORTED"
            reason = "证据可信度不足。"

        return {
            "capability_judgement": {
                "status": status,
                "reason": reason,
                "evidence_refs": [item.get("chunk_id", "") for item in evidence_pack],
            }
        }

