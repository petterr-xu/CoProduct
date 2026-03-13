from __future__ import annotations

from typing import Any, Protocol


class StructuredModel(Protocol):
    """Protocol for schema-constrained text generation."""

    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type) -> Any:
        """Return structured output validated against the requested schema."""


class EmbeddingModel(Protocol):
    """Protocol for text embedding capability."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return dense vectors for input texts."""


class RerankerModel(Protocol):
    """Protocol for candidate reranking capability."""

    def rerank(self, query: str, candidates: list[str]) -> list[int]:
        """Return candidate indices sorted from most to least relevant."""

