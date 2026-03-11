from pydantic import BaseModel, Field

from app.schemas.analysis import ImpactItemSchema, MissingInfoItemSchema, RiskItemSchema
from app.schemas.capability import CapabilityJudgementSchema
from app.schemas.evidence import EvidenceItemSchema
from app.schemas.requirement import RequirementSchema


class ReportSchema(BaseModel):
    summary: str = ""
    capabilityJudgement: CapabilityJudgementSchema = Field(default_factory=CapabilityJudgementSchema)
    structuredDraft: RequirementSchema = Field(default_factory=RequirementSchema)
    evidence: list[EvidenceItemSchema] = Field(default_factory=list)
    missingInfoItems: list[MissingInfoItemSchema] = Field(default_factory=list)
    riskItems: list[RiskItemSchema] = Field(default_factory=list)
    impactItems: list[ImpactItemSchema] = Field(default_factory=list)
    nextSteps: list[str] = Field(default_factory=list)
