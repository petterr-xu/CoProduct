from __future__ import annotations

import json
import time
from typing import Any

from app.core.logging import log_event
from app.model_client.heuristic import HeuristicModelClient
from app.model_client.language_guard import enforce_output_language
from app.model_client.providers.base import ChatProvider
from app.model_client.structured_output import invoke_with_validation
from app.prompts import build_structured_prompt


class CloudModelClient:
    """Cloud-backed model client with heuristic fallback for robustness."""

    def __init__(
        self,
        *,
        provider: ChatProvider,
        max_structured_retries: int = 1,
        temperature: float = 0.0,
        log_output_enabled: bool = True,
        log_output_max_chars: int = 4000,
        output_language: str = "zh-CN",
        enforce_output_language_check: bool = True,
        embedding_fallback: HeuristicModelClient | None = None,
    ) -> None:
        self.provider = provider
        self.max_structured_retries = max_structured_retries
        self.temperature = temperature
        self.log_output_enabled = log_output_enabled
        self.log_output_max_chars = max(200, log_output_max_chars)
        self.output_language = output_language
        self.enforce_output_language_check = enforce_output_language_check
        self.embedding_fallback = embedding_fallback or HeuristicModelClient()

    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type) -> Any:
        start = time.perf_counter()
        prompt_build = build_structured_prompt(
            prompt_name=prompt_name,
            input_data=input_data,
            schema=schema,
            output_language=self.output_language,
        )

        attempt = invoke_with_validation(
            prompt_name=prompt_name,
            schema=schema,
            max_retries=self.max_structured_retries,
            base_prompt=prompt_build.prompt_text,
            invoke_text=lambda effective_prompt: self.provider.invoke_text(
                prompt=effective_prompt, temperature=self.temperature
            ),
        )
        enforce_output_language(
            prompt_name=prompt_name,
            payload=attempt.validated_payload,
            output_language=self.output_language,
            enforce=self.enforce_output_language_check,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_fields: dict[str, Any] = {
            "prompt_name": prompt_name,
            "latency_ms": latency_ms,
            "token_input_estimate": len(json.dumps(input_data, ensure_ascii=False)),
            "token_output_estimate": len(json.dumps(attempt.validated_payload, ensure_ascii=False)),
            "provider": "cloud",
            "prompt_hash": prompt_build.prompt_hash,
            "schema_name": prompt_build.schema_name,
        }
        if self.log_output_enabled:
            log_fields["raw_output_preview"] = self._truncate_for_log(attempt.raw_text)
            log_fields["validated_output_preview"] = self._truncate_for_log(
                json.dumps(attempt.validated_payload, ensure_ascii=False)
            )

        log_event(
            "model_structured_invoke",
            **log_fields,
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

    def _truncate_for_log(self, text: str) -> str:
        if len(text) <= self.log_output_max_chars:
            return text
        return f"{text[: self.log_output_max_chars]}...(truncated)"
