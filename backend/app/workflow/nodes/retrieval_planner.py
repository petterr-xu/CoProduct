from __future__ import annotations

from app.model_client.base import ModelClient
from app.schemas import RetrievalPlanSchema
from app.workflow.state import PreReviewState


class RetrievalPlannerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        normalized = state.get("normalized_request", {})
        retrieval_plan = self.model_client.structured_invoke(
            prompt_name="retrieval_planner",
            input_data={
                "requirement_text": normalized.get("requirement_text", ""),
                "parsed_requirement": state.get("parsed_requirement", {}),
                "business_domain": normalized.get("business_domain"),
                "module_hint": normalized.get("module_hint"),
            },
            schema=RetrievalPlanSchema,
        )
        return {"retrieval_plan": retrieval_plan}
