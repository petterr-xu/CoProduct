from __future__ import annotations

from app.workflow.state import PreReviewState


class RiskAnalyzerNode:
    def __call__(self, state: PreReviewState) -> dict:
        merged_text = state.get("normalized_request", {}).get("merged_text", "")
        risk_items: list[dict] = []

        if "导出" in merged_text and ("手机号" in merged_text or "用户" in merged_text):
            risk_items.append(
                {
                    "type": "permission_and_security",
                    "description": "导出用户相关信息可能触发敏感数据风险。",
                    "level": "HIGH",
                }
            )
        if "批量" in merged_text:
            risk_items.append(
                {
                    "type": "implementation_complexity",
                    "description": "批量处理可能引入性能与资源竞争问题。",
                    "level": "MEDIUM",
                }
            )

        return {"risk_items": risk_items}

