from pydantic import BaseModel, Field


class RetrievalPlanSchema(BaseModel):
    queries: list[str] = Field(default_factory=list)
    source_filters: dict = Field(default_factory=dict)
    module_tags: list[str] = Field(default_factory=list)

