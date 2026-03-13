"""Evidence item contract shared by retrieval/selection/report stages."""

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceItemSchema(BaseModel):
    """Single evidence unit shown in report and used for capability decisions."""

    doc_id: str = Field(description="Document identifier in the knowledge base.")
    doc_title: str = Field(description="Document title for UI display.")
    chunk_id: str = Field(description="Chunk identifier used as stable evidence reference.")
    snippet: str = Field(description="Selected evidence snippet.")
    source_type: Literal["product_doc", "api_doc", "constraint_doc", "case"] = Field(
        description="Evidence source category.",
    )
    relevance_score: float = Field(description="Retriever/reranker relevance score.")
    trust_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Evidence trust level.")
