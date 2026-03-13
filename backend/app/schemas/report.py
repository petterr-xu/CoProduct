"""Final report contract persisted to DB and returned to frontend detail view."""

from pydantic import BaseModel, Field

from app.schemas.analysis import ImpactItemSchema, MissingInfoItemSchema, RiskItemSchema
from app.schemas.capability import CapabilityJudgementSchema
from app.schemas.evidence import EvidenceItemSchema
from app.schemas.requirement import RequirementSchema


class ReportSchema(BaseModel):
    """Unified report payload produced by `report_composer` node."""

    summary: str = Field(default="", description="Executive summary text.")
    capabilityJudgement: CapabilityJudgementSchema = Field(
        default_factory=CapabilityJudgementSchema,
        description="Capability decision section.",
    )
    structuredDraft: RequirementSchema = Field(
        default_factory=RequirementSchema,
        description="Normalized requirement section.",
    )
    evidence: list[EvidenceItemSchema] = Field(default_factory=list, description="Supporting evidence list.")
    missingInfoItems: list[MissingInfoItemSchema] = Field(
        default_factory=list,
        description="Information gaps requiring follow-up.",
    )
    riskItems: list[RiskItemSchema] = Field(default_factory=list, description="Identified risk items.")
    impactItems: list[ImpactItemSchema] = Field(default_factory=list, description="Impacted module list.")
    nextSteps: list[str] = Field(default_factory=list, description="Suggested follow-up actions.")
