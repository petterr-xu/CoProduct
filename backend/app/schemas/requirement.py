from pydantic import BaseModel, Field


class RequirementSchema(BaseModel):
    goal: str = ""
    actors: list[str] = Field(default_factory=list)
    business_objects: list[str] = Field(default_factory=list)
    data_objects: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    expected_output: str = ""
    uncertain_points: list[str] = Field(default_factory=list)

