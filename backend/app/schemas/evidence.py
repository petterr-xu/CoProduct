from pydantic import BaseModel


class EvidenceItemSchema(BaseModel):
    doc_id: str
    doc_title: str
    chunk_id: str
    snippet: str
    source_type: str
    relevance_score: float
    trust_level: str

