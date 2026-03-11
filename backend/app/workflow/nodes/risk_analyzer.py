from __future__ import annotations

import time

from app.core.logging import log_event
from app.model_client.base import ModelClient
from app.schemas import RiskItemSchema
from app.workflow.state import PreReviewState


class RiskAnalyzerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        start = time.perf_counter()
        try:
            items = self.model_client.structured_invoke(
                prompt_name="risk_analyzer",
                input_data={"merged_text": state.get("normalized_request", {}).get("merged_text", "")},
                schema=list,
            )
            validated = [RiskItemSchema.model_validate(item).model_dump() for item in items]
            log_event(
                "node_completed",
                node_name="risk_analyzer",
                session_id=state.get("session_id"),
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
            return {"risk_items": validated}
        except Exception as exc:  # noqa: BLE001
            log_event(
                "node_degraded",
                node_name="risk_analyzer",
                session_id=state.get("session_id"),
                latency_ms=int((time.perf_counter() - start) * 1000),
                error_code="WORKFLOW_ERROR",
                error_message=str(exc),
            )
            return {"risk_items": []}
