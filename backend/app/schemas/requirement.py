"""Requirement parsing contract used between parser node and downstream analyzers."""

from pydantic import BaseModel, Field


class RequirementSchema(BaseModel):
    """Normalized requirement view produced by `requirement_parser` node."""

    goal: str = Field(default="", description="Primary business goal in one concise sentence.")
    actors: list[str] = Field(default_factory=list, description="Roles/users directly involved in this requirement.")
    business_objects: list[str] = Field(default_factory=list, description="Business entities/processes in scope.")
    data_objects: list[str] = Field(default_factory=list, description="Data entities touched by the requirement.")
    constraints: list[str] = Field(default_factory=list, description="Explicit constraints such as permissions or SLA.")
    expected_output: str = Field(default="", description="Expected delivery/output artifact.")
    uncertain_points: list[str] = Field(
        default_factory=list,
        description="Ambiguities or missing facts that reduce implementation confidence.",
    )
