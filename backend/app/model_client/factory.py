from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings
from app.model_client.base import ModelClient
from app.model_client.heuristic import HeuristicModelClient


@lru_cache(maxsize=1)
def _build_model_client() -> ModelClient:
    return HeuristicModelClient()


def build_model_client(_settings: Settings | None = None) -> ModelClient:
    """Build model client singleton for workflow nodes.

    M2 keeps a deterministic local client. This factory is the extension point
    for cloud model providers in later milestones.
    """

    return _build_model_client()
