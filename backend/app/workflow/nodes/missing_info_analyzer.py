from __future__ import annotations

from app.workflow.state import PreReviewState


class MissingInfoAnalyzerNode:
    def __call__(self, state: PreReviewState) -> dict:
        parsed = state.get("parsed_requirement", {})
        merged_text = state.get("normalized_request", {}).get("merged_text", "")

        items: list[dict] = []
        if not parsed.get("actors"):
            items.append(
                {
                    "type": "target_user",
                    "question": "目标用户是谁？",
                    "priority": "HIGH",
                }
            )
        if "权限" not in merged_text and "角色" not in merged_text:
            items.append(
                {
                    "type": "permission_boundary",
                    "question": "不同角色的权限边界是什么？",
                    "priority": "HIGH",
                }
            )
        if "时效" not in merged_text and "时间" not in merged_text:
            items.append(
                {
                    "type": "time_requirement",
                    "question": "是否有明确的时间要求？",
                    "priority": "MEDIUM",
                }
            )
        if "性能" not in merged_text and "量级" not in merged_text:
            items.append(
                {
                    "type": "performance_requirement",
                    "question": "预计数据规模和性能目标是什么？",
                    "priority": "MEDIUM",
                }
            )

        return {"missing_info_items": items}

