"""Capability judgement contract used for final support decision."""

from typing import Literal

from pydantic import BaseModel, Field


class CapabilityJudgementSchema(BaseModel):
    """Capability verdict emitted by `capability_judge` node."""

    status: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED", "NEED_MORE_INFO"] = Field(
        default="NEED_MORE_INFO",
        description="Final support status for the requested capability.",
    )
    reason: str = Field(default="", description="Human-readable rationale for the status.")
    confidence: Literal["high", "medium", "low"] = Field(
        default="low",
        description="Confidence level of the judgement.",
    )
    evidence_refs: list[str] = Field(default_factory=list, description="Chunk IDs supporting this judgement.")
