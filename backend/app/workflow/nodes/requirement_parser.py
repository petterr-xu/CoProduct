from __future__ import annotations

from app.model_client.base import ModelClient
from app.schemas import RequirementSchema
from app.workflow.state import PreReviewState


class RequirementParserNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        parsed = self.model_client.structured_invoke(
            prompt_name="requirement_parser",
            input_data={"merged_text": state.get("normalized_request", {}).get("merged_text", "")},
            schema=RequirementSchema,
        )
        return {"parsed_requirement": parsed}
