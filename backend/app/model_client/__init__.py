"""Model client abstraction and default implementation."""

from app.model_client.base import ModelClient
from app.model_client.factory import build_model_client
from app.model_client.interfaces import EmbeddingModel, RerankerModel, StructuredModel

__all__ = [
    "ModelClient",
    "StructuredModel",
    "EmbeddingModel",
    "RerankerModel",
    "build_model_client",
]
