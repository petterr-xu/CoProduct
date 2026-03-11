from __future__ import annotations

from app.model_client.base import ModelClient
from app.schemas import ImpactItemSchema
from app.workflow.state import PreReviewState


class ImpactAnalyzerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        items = self.model_client.structured_invoke(
            prompt_name="impact_analyzer",
            input_data={
                "parsed_requirement": state.get("parsed_requirement", {}),
                "module_hint": state.get("normalized_request", {}).get("module_hint"),
            },
            schema=list,
        )
        merged_reasons: dict[str, list[str]] = {}
        for item in items:
            validated = ImpactItemSchema.model_validate(item).model_dump()
            module = validated["module"]
            merged_reasons.setdefault(module, [])
            reason = validated["reason"]
            if reason not in merged_reasons[module]:
                merged_reasons[module].append(reason)

        result = [{"module": module, "reason": "；".join(reasons)} for module, reasons in merged_reasons.items()]
        return {"impact_items": result}
