from __future__ import annotations

from app.workflow.state import PreReviewState


class RetrievalPlannerNode:
    def __call__(self, state: PreReviewState) -> dict:
        parsed = state["parsed_requirement"]
        normalized = state["normalized_request"]
        requirement_text = normalized.get("requirement_text", "")

        queries = [
            f"{requirement_text} 能力",
            f"{requirement_text} API",
            f"{requirement_text} 限制 风险",
        ]
        if parsed.get("uncertain_points"):
            queries.append(f"{requirement_text} 相似案例")

        retrieval_plan = {
            "queries": queries[:5],
            "source_filters": {
                "business_domain": normalized.get("business_domain"),
                "module_hint": normalized.get("module_hint"),
            },
            "module_tags": parsed.get("business_objects", []),
        }
        return {"retrieval_plan": retrieval_plan}

