from __future__ import annotations

from app.model_client.base import ModelClient
from app.schemas import MissingInfoListSchema
from app.workflow.state import PreReviewState


class MissingInfoAnalyzerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        try:
            result = self.model_client.structured_invoke(
                prompt_name="missing_info_analyzer",
                input_data={
                    "parsed_requirement": state.get("parsed_requirement", {}),
                    "merged_text": state.get("normalized_request", {}).get("merged_text", ""),
                },
                schema=MissingInfoListSchema,
            )
            validated = MissingInfoListSchema.model_validate(result).model_dump()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"MODEL_SCHEMA_ERROR: missing_info_analyzer output invalid: {exc}") from exc
        return {"missing_info_items": validated["items"]}
