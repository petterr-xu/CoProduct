from __future__ import annotations

from app.model_client.base import ModelClient
from app.schemas import RiskItemSchema
from app.workflow.state import PreReviewState


class RiskAnalyzerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        items = self.model_client.structured_invoke(
            prompt_name="risk_analyzer",
            input_data={"merged_text": state.get("normalized_request", {}).get("merged_text", "")},
            schema=list,
        )
        validated = [RiskItemSchema.model_validate(item).model_dump() for item in items]
        return {"risk_items": validated}
