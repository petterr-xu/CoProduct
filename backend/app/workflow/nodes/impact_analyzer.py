from __future__ import annotations

import time

from app.core.logging import log_event
from app.model_client.base import ModelClient
from app.schemas import ImpactItemSchema
from app.workflow.state import PreReviewState


class ImpactAnalyzerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        start = time.perf_counter()
        try:
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
            log_event(
                "node_completed",
                node_name="impact_analyzer",
                session_id=state.get("session_id"),
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
            return {"impact_items": result}
        except Exception as exc:  # noqa: BLE001
            log_event(
                "node_degraded",
                node_name="impact_analyzer",
                session_id=state.get("session_id"),
                latency_ms=int((time.perf_counter() - start) * 1000),
                error_code="WORKFLOW_ERROR",
                error_message=str(exc),
            )
            return {"impact_items": []}
