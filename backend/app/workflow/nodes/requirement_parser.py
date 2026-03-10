from __future__ import annotations

from app.workflow.state import PreReviewState


class RequirementParserNode:
    def __call__(self, state: PreReviewState) -> dict:
        merged_text = state["normalized_request"].get("merged_text", "")

        actors: list[str] = []
        business_objects: list[str] = []
        data_objects: list[str] = []
        constraints: list[str] = []
        uncertain_points: list[str] = []
        expected_output = ""
        goal = ""

        if "运营" in merged_text:
            actors.append("运营")
        if "产品" in merged_text:
            actors.append("产品")
        if "导出" in merged_text:
            goal = "支持导出能力"
            expected_output = "导出文件"
            business_objects.append("导出任务")
        if "活动" in merged_text:
            business_objects.append("活动")
        if "报名" in merged_text:
            business_objects.append("报名")
            data_objects.append("报名记录")
        if "权限" in merged_text or "角色" in merged_text:
            constraints.append("角色权限边界")

        if not goal:
            uncertain_points.append("业务目标不明确")
        if "角色" not in merged_text and "权限" not in merged_text:
            uncertain_points.append("权限边界不明确")
        if "时间" not in merged_text and "时效" not in merged_text:
            uncertain_points.append("时间要求不明确")

        parsed = {
            "goal": goal,
            "actors": sorted(list(set(actors))),
            "business_objects": sorted(list(set(business_objects))),
            "data_objects": sorted(list(set(data_objects))),
            "constraints": sorted(list(set(constraints))),
            "expected_output": expected_output,
            "uncertain_points": sorted(list(set(uncertain_points))),
        }
        return {"parsed_requirement": parsed}

