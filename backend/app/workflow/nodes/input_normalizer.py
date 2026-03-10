from __future__ import annotations

from app.core.config import Settings
from app.utils.text import clean_text, truncate_text
from app.workflow.state import PreReviewState


class InputNormalizerNode:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def __call__(self, state: PreReviewState) -> dict:
        raw = state.get("normalized_request", {})
        requirement_text = clean_text(raw.get("requirement_text", ""))
        background_text = clean_text(raw.get("background_text", ""))
        additional_context = clean_text(raw.get("additional_context", ""))

        merged = requirement_text
        if background_text:
            merged = f"{merged}\n背景：{background_text}"
        if additional_context:
            merged = f"{merged}\n补充：{additional_context}"

        merged = truncate_text(merged, self.settings.normalized_text_limit)

        return {
            "normalized_request": {
                "requirement_text": requirement_text,
                "background_text": background_text,
                "additional_context": additional_context,
                "business_domain": raw.get("business_domain"),
                "module_hint": raw.get("module_hint"),
                "attachments": raw.get("attachments", []),
                "merged_text": merged,
            }
        }

