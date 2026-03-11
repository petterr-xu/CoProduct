from typing import Literal

from pydantic import BaseModel, Field


class CapabilityJudgementSchema(BaseModel):
    status: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED", "NEED_MORE_INFO"] = "NEED_MORE_INFO"
    reason: str = ""
    confidence: Literal["high", "medium", "low"] = "low"
    evidence_refs: list[str] = Field(default_factory=list)
