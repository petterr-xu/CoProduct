from __future__ import annotations

from typing import Protocol


class ChatProvider(Protocol):
    """Provider protocol for chat completion and embedding operations."""

    def invoke_text(self, *, prompt: str, temperature: float = 0.0) -> str:
        """Return plain text content from a chat completion request."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for input texts."""

