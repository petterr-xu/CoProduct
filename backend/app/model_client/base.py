from __future__ import annotations

from typing import Any, Protocol


class ModelClient(Protocol):
    """Unified interface for model capabilities used by workflow nodes."""

    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type) -> Any:
        """Return schema-conforming structured output."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return vector embeddings for retrieval and similarity tasks."""

    def rerank(self, query: str, candidates: list[str]) -> list[int]:
        """Return candidate indices sorted from most to least relevant."""

