from __future__ import annotations

import time

from app.core.logging import log_event
from app.model_client.base import ModelClient
from app.schemas import ImpactListSchema
from app.workflow.state import PreReviewState


class ImpactAnalyzerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        start = time.perf_counter()
        try:
            response = self.model_client.structured_invoke(
                prompt_name="impact_analyzer",
                input_data={
                    "parsed_requirement": state.get("parsed_requirement", {}),
                    "module_hint": state.get("normalized_request", {}).get("module_hint"),
                },
                schema=ImpactListSchema,
            )
            validated = ImpactListSchema.model_validate(response).model_dump()
            merged_reasons: dict[str, list[str]] = {}
            for item in validated["items"]:
                module = item["module"]
                merged_reasons.setdefault(module, [])
                reason = item["reason"]
                if reason not in merged_reasons[module]:
                    merged_reasons[module].append(reason)

            merged_items = [{"module": module, "reason": "；".join(reasons)} for module, reasons in merged_reasons.items()]
            log_event(
                "node_completed",
                node_name="impact_analyzer",
                session_id=state.get("session_id"),
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
            return {"impact_items": merged_items}
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"MODEL_SCHEMA_ERROR: impact_analyzer output invalid: {exc}") from exc
