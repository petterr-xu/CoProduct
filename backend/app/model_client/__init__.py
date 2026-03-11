"""Model client abstraction and default implementation."""

from app.model_client.base import ModelClient
from app.model_client.factory import build_model_client

__all__ = ["ModelClient", "build_model_client"]

