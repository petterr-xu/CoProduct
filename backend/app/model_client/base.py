from __future__ import annotations

from typing import Protocol

from app.model_client.interfaces import EmbeddingModel, RerankerModel, StructuredModel


class ModelClient(StructuredModel, EmbeddingModel, RerankerModel, Protocol):
    """Backward-compatible composite protocol used by workflow and RAG layers."""
