"""Retrieval planning contract produced by `retrieval_planner` node."""

from pydantic import BaseModel, Field


class RetrievalPlanSchema(BaseModel):
    """Search plan consumed by the retrieval stage."""

    queries: list[str] = Field(default_factory=list, description="Ordered retrieval queries for evidence lookup.")
    source_filters: dict = Field(default_factory=dict, description="Optional source constraints for retrieval backend.")
    module_tags: list[str] = Field(default_factory=list, description="Module/business tags used for narrowing search.")
