from __future__ import annotations

from app.model_client.base import ModelClient
from app.schemas import ReportSchema
from app.workflow.state import PreReviewState


class ReportComposerNode:
    def __init__(self, model_client: ModelClient) -> None:
        self.model_client = model_client

    def __call__(self, state: PreReviewState) -> dict:
        report = self.model_client.structured_invoke(
            prompt_name="report_composer",
            input_data={
                "parsed_requirement": state.get("parsed_requirement", {}),
                "capability_judgement": state.get("capability_judgement", {}),
                "evidence_pack": state.get("evidence_pack", []),
                "missing_info_items": state.get("missing_info_items", []),
                "risk_items": state.get("risk_items", []),
                "impact_items": state.get("impact_items", []),
            },
            schema=ReportSchema,
        )
        return {"report": report}
