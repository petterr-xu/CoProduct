from typing import Literal

from pydantic import BaseModel


class EvidenceItemSchema(BaseModel):
    doc_id: str
    doc_title: str
    chunk_id: str
    snippet: str
    source_type: Literal["product_doc", "api_doc", "constraint_doc", "case"]
    relevance_score: float
    trust_level: Literal["HIGH", "MEDIUM", "LOW"]
