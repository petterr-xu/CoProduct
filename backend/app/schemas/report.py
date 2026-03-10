from pydantic import BaseModel, Field


class ReportSchema(BaseModel):
    summary: str = ""
    capabilityJudgement: dict = Field(default_factory=dict)
    structuredDraft: dict = Field(default_factory=dict)
    evidence: list[dict] = Field(default_factory=list)
    missingInfoItems: list[dict] = Field(default_factory=list)
    riskItems: list[dict] = Field(default_factory=list)
    impactItems: list[dict] = Field(default_factory=list)
    nextSteps: list[str] = Field(default_factory=list)

