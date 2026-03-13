from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel

from app.core.logging import log_event
from app.model_client.heuristic import HeuristicModelClient
from app.model_client.providers.base import ChatProvider
from app.model_client.structured_output import invoke_with_validation


def _schema_hint(schema: type) -> str:
    if schema is list:
        return "Return a JSON array."
    if schema is dict:
        return "Return a JSON object."
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        fields = ", ".join(schema.model_fields.keys())
        return f"Return a JSON object matching `{schema.__name__}` with fields: {fields}."
    return "Return valid JSON."


def _build_structured_prompt(prompt_name: str, input_data: dict, schema: type) -> str:
    return (
        "You are a backend agent node. Produce structured output only.\n"
        f"Node: {prompt_name}\n"
        f"{_schema_hint(schema)}\n"
        "Output rules:\n"
        "- JSON only.\n"
        "- No markdown.\n"
        "- Do not invent unsupported enum values.\n"
        "Input payload:\n"
        f"{json.dumps(input_data, ensure_ascii=False)}"
    )


class CloudModelClient:
    """Cloud-backed model client with heuristic fallback for robustness."""

    def __init__(
        self,
        *,
        provider: ChatProvider,
        max_structured_retries: int = 1,
        temperature: float = 0.0,
        embedding_fallback: HeuristicModelClient | None = None,
    ) -> None:
        self.provider = provider
        self.max_structured_retries = max_structured_retries
        self.temperature = temperature
        self.embedding_fallback = embedding_fallback or HeuristicModelClient()

    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type) -> Any:
        start = time.perf_counter()
        prompt = _build_structured_prompt(prompt_name, input_data, schema)

        attempt = invoke_with_validation(
            prompt_name=prompt_name,
            schema=schema,
            max_retries=self.max_structured_retries,
            base_prompt=prompt,
            invoke_text=lambda effective_prompt: self.provider.invoke_text(
                prompt=effective_prompt, temperature=self.temperature
            ),
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_event(
            "model_structured_invoke",
            prompt_name=prompt_name,
            latency_ms=latency_ms,
            token_input_estimate=len(json.dumps(input_data, ensure_ascii=False)),
            token_output_estimate=len(json.dumps(attempt.validated_payload, ensure_ascii=False)),
            provider="cloud",
        )
        return attempt.validated_payload

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        start = time.perf_counter()
        provider_used = "cloud"
        try:
            vectors = self.provider.embed_texts(texts)
        except Exception:  # noqa: BLE001
            provider_used = "heuristic_fallback"
            vectors = self.embedding_fallback.embed_texts(texts)

        latency_ms = int((time.perf_counter() - start) * 1000)
        log_event(
            "model_embed_texts",
            latency_ms=latency_ms,
            text_count=len(texts),
            provider=provider_used,
        )
        return vectors

    def rerank(self, query: str, candidates: list[str]) -> list[int]:
        # Phase 1 keeps rerank deterministic to avoid cloud variability and extra cost.
        return self.embedding_fallback.rerank(query, candidates)

