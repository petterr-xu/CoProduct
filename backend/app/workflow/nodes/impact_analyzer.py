from __future__ import annotations

from app.workflow.state import PreReviewState


class ImpactAnalyzerNode:
    def __call__(self, state: PreReviewState) -> dict:
        parsed = state.get("parsed_requirement", {})
        normalized = state.get("normalized_request", {})

        module_hint = normalized.get("module_hint")
        impacts: list[dict] = []
        if module_hint:
            impacts.append({"module": module_hint, "reason": "模块标签命中"})

        for obj in parsed.get("business_objects", []):
            if obj == "导出任务":
                impacts.append({"module": "export_service", "reason": "导出能力相关"})
            if obj == "报名":
                impacts.append({"module": "registration", "reason": "业务对象命中"})

        merged_reasons: dict[str, list[str]] = {}
        for item in impacts:
            module = item["module"]
            merged_reasons.setdefault(module, [])
            if item["reason"] not in merged_reasons[module]:
                merged_reasons[module].append(item["reason"])

        result = [{"module": module, "reason": "；".join(reasons)} for module, reasons in merged_reasons.items()]
        return {"impact_items": result}
