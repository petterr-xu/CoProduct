from __future__ import annotations

from app.workflow.state import PreReviewState


class ReportComposerNode:
    def __call__(self, state: PreReviewState) -> dict:
        parsed = state.get("parsed_requirement", {})
        capability = state.get("capability_judgement", {})
        missing = state.get("missing_info_items", [])
        risks = state.get("risk_items", [])
        impacts = state.get("impact_items", [])
        evidence = state.get("evidence_pack", [])

        summary = (
            f"目标：{parsed.get('goal') or '待补充'}；"
            f"能力判断：{capability.get('status', 'NEED_MORE_INFO')}；"
            f"待补充项：{len(missing)} 条。"
        )

        report = {
            "summary": summary,
            "capabilityJudgement": capability,
            "structuredDraft": parsed,
            "evidence": evidence,
            "missingInfoItems": missing,
            "riskItems": risks,
            "impactItems": impacts,
            "nextSteps": [
                "优先补齐高优先级缺失信息。",
                "对高风险项补充约束后再进入正式评审。",
            ],
        }
        return {"report": report}

