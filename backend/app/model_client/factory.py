from __future__ import annotations

from functools import lru_cache

from app.core.logging import log_event
from app.core.config import Settings
from app.model_client.base import ModelClient
from app.model_client.cloud import CloudModelClient
from app.model_client.heuristic import HeuristicModelClient
from app.model_client.providers import OpenAICompatibleProvider


@lru_cache(maxsize=8)
def _build_model_client_cached(
    *,
    model_mode: str,
    model_provider: str,
    model_api_key: str | None,
    model_base_url: str,
    model_chat_model: str,
    model_embedding_model: str | None,
    model_timeout_seconds: float,
    model_structured_retries: int,
    model_temperature: float,
    model_log_output_enabled: bool,
    model_log_output_max_chars: int,
) -> ModelClient:
    if model_mode == "heuristic":
        return HeuristicModelClient()

    if model_mode != "cloud":
        raise RuntimeError(f"unsupported COPRODUCT_MODEL_MODE: {model_mode}")

    if model_provider != "openai_compatible":
        raise RuntimeError(f"unsupported COPRODUCT_MODEL_PROVIDER: {model_provider}")
    if not model_api_key:
        raise RuntimeError("COPRODUCT_MODEL_API_KEY is required when COPRODUCT_MODEL_MODE=cloud")

    provider = OpenAICompatibleProvider(
        api_key=model_api_key,
        base_url=model_base_url,
        chat_model=model_chat_model,
        embedding_model=model_embedding_model,
        timeout_seconds=model_timeout_seconds,
    )
    return CloudModelClient(
        provider=provider,
        max_structured_retries=model_structured_retries,
        temperature=model_temperature,
        log_output_enabled=model_log_output_enabled,
        log_output_max_chars=model_log_output_max_chars,
    )


def build_model_client(_settings: Settings | None = None) -> ModelClient:
    """Build singleton model client with `heuristic/cloud` runtime switch."""
    settings = _settings or Settings()
    client = _build_model_client_cached(
        model_mode=settings.model_mode,
        model_provider=settings.model_provider,
        model_api_key=settings.model_api_key,
        model_base_url=settings.model_base_url,
        model_chat_model=settings.model_chat_model,
        model_embedding_model=settings.model_embedding_model,
        model_timeout_seconds=settings.model_timeout_seconds,
        model_structured_retries=settings.model_structured_retries,
        model_temperature=settings.model_temperature,
        model_log_output_enabled=settings.model_log_output_enabled,
        model_log_output_max_chars=settings.model_log_output_max_chars,
    )
    log_event(
        "model_client_built",
        mode=settings.model_mode,
        provider=settings.model_provider,
        chat_model=settings.model_chat_model,
        embedding_model=settings.model_embedding_model,
    )
    return client
