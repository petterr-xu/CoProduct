from __future__ import annotations

from typing import Any

import httpx


class OpenAICompatibleProvider:
    """OpenAI-compatible adapter used for DeepSeek/OpenAI style APIs."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        chat_model: str,
        embedding_model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.timeout_seconds = timeout_seconds

    def invoke_text(self, *, prompt: str, temperature: float = 0.0) -> str:
        payload = {
            "model": self.chat_model,
            "messages": [
                {"role": "system", "content": "You are a precise assistant that returns useful output."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        data = self._post_json("/chat/completions", payload)
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("provider returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("provider returned empty content")
        return content

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.embedding_model:
            raise RuntimeError("embedding model is not configured")

        payload = {"model": self.embedding_model, "input": texts}
        data = self._post_json("/embeddings", payload)
        records = data.get("data") or []
        if not isinstance(records, list):
            raise RuntimeError("provider returned invalid embeddings payload")

        vectors: list[list[float]] = []
        for record in records:
            embedding = record.get("embedding")
            if not isinstance(embedding, list):
                raise RuntimeError("provider returned invalid embedding vector")
            vectors.append([float(value) for value in embedding])
        return vectors

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise RuntimeError(f"provider http error: status={response.status_code} body={response.text[:500]}")

        try:
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("provider response is not valid json") from exc

        if not isinstance(data, dict):
            raise RuntimeError("provider response json must be an object")
        return data

