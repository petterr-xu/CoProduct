"""Analysis stage contracts: missing-info, risk, and impact outputs."""

from typing import Literal

from pydantic import BaseModel, Field


class MissingInfoItemSchema(BaseModel):
    """One actionable missing-information question for the requester."""

    type: str = Field(description="Stable missing-info category identifier.")
    question: str = Field(description="Question that user can directly answer.")
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Resolution priority.")


class MissingInfoListSchema(BaseModel):
    """Top-level strict container used by model structured output."""

    items: list[MissingInfoItemSchema] = Field(default_factory=list, description="Missing-info checklist items.")


class RiskItemSchema(BaseModel):
    """Single risk statement extracted from requirement context."""

    type: str = Field(description="Risk category identifier.")
    description: str = Field(description="Concrete risk description.")
    level: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Risk severity level.")


class RiskListSchema(BaseModel):
    """Top-level strict container used by risk analyzer structured output."""

    items: list[RiskItemSchema] = Field(default_factory=list, description="Risk items.")


class ImpactItemSchema(BaseModel):
    """Single impacted module record."""

    module: str = Field(description="Impacted module name/identifier.")
    reason: str = Field(description="Why this module is impacted.")


class ImpactListSchema(BaseModel):
    """Top-level strict container used by impact analyzer structured output."""

    items: list[ImpactItemSchema] = Field(default_factory=list, description="Impact items.")
