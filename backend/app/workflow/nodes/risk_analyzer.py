from __future__ import annotations

import time

from app.core.logging import log_event
from app.model_client.base import ModelClient
from app.schemas import RiskListSchema
from app.workflow.state import PreReviewState


class RiskAnalyzerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        start = time.perf_counter()
        try:
            result = self.model_client.structured_invoke(
                prompt_name="risk_analyzer",
                input_data={"merged_text": state.get("normalized_request", {}).get("merged_text", "")},
                schema=RiskListSchema,
            )
            validated = RiskListSchema.model_validate(result).model_dump()
            log_event(
                "node_completed",
                node_name="risk_analyzer",
                session_id=state.get("session_id"),
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
            return {"risk_items": validated["items"]}
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"MODEL_SCHEMA_ERROR: risk_analyzer output invalid: {exc}") from exc
