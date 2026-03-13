from typing import Literal

from pydantic import BaseModel


class MissingInfoItemSchema(BaseModel):
    type: str
    question: str
    priority: Literal["HIGH", "MEDIUM", "LOW"]


class MissingInfoListSchema(BaseModel):
    items: list[MissingInfoItemSchema]


class RiskItemSchema(BaseModel):
    type: str
    description: str
    level: Literal["HIGH", "MEDIUM", "LOW"]


class ImpactItemSchema(BaseModel):
    module: str
    reason: str
