from __future__ import annotations

from pydantic import BaseModel

from app.core.config import Settings
from app.model_client.cloud import CloudModelClient
from app.model_client.factory import build_model_client
from app.model_client.heuristic import HeuristicModelClient
from app.model_client.structured_output import invoke_with_validation
from app.prompts import build_structured_prompt, load_prompt_template
from app.schemas import MissingInfoListSchema


class _SimpleSchema(BaseModel):
    value: str


class _StubProvider:
    def __init__(self, responses: list[str], embedding_should_fail: bool = False) -> None:
        self.responses = responses
        self.embedding_should_fail = embedding_should_fail
        self.call_count = 0
        self.last_prompt: str | None = None

    def invoke_text(self, *, prompt: str, temperature: float = 0.0) -> str:  # noqa: ARG002
        self.last_prompt = prompt
        index = min(self.call_count, len(self.responses) - 1)
        self.call_count += 1
        return self.responses[index]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.embedding_should_fail:
            raise RuntimeError("embedding endpoint unavailable")
        return [[0.1, 0.2, 0.3] for _ in texts]


def test_structured_output_retry_and_repair() -> None:
    provider = _StubProvider(responses=["not-json", '{"value": "ok"}'])

    attempt = invoke_with_validation(
        prompt_name="unit_test_node",
        schema=_SimpleSchema,
        base_prompt="base prompt",
        max_retries=1,
        invoke_text=lambda prompt: provider.invoke_text(prompt=prompt),
    )

    assert attempt.validated_payload == {"value": "ok"}
    assert provider.call_count == 2


def test_build_model_client_returns_heuristic_by_default() -> None:
    settings = Settings(model_mode="heuristic")
    client = build_model_client(settings)
    assert isinstance(client, HeuristicModelClient)


def test_build_model_client_cloud_requires_api_key() -> None:
    settings = Settings(
        model_mode="cloud",
        model_provider="openai_compatible",
        model_api_key=None,
    )
    try:
        build_model_client(settings)
    except RuntimeError as exc:
        assert "COPRODUCT_MODEL_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected model factory to reject cloud mode without api key")


def test_cloud_model_client_embedding_fallback_to_heuristic() -> None:
    provider = _StubProvider(responses=['{"value":"ok"}'], embedding_should_fail=True)
    client = CloudModelClient(provider=provider, embedding_fallback=HeuristicModelClient(embedding_dim=8))

    vectors = client.embed_texts(["hello world"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 8


def test_prompt_template_loader_reads_node_prompt() -> None:
    text = load_prompt_template("missing_info_analyzer")
    assert "missing_info_analyzer" in text
    assert "Hard Constraints" in text


def test_structured_prompt_composer_includes_schema_contract_and_payload() -> None:
    result = build_structured_prompt(
        prompt_name="missing_info_analyzer",
        input_data={"merged_text": "need export capability", "parsed_requirement": {}},
        schema=MissingInfoListSchema,
    )
    assert result.prompt_name == "missing_info_analyzer"
    assert result.schema_name == "MissingInfoListSchema"
    assert "JSON Schema" in result.prompt_text
    assert "Input Payload (JSON)" in result.prompt_text
    assert len(result.prompt_hash) == 12


def test_cloud_model_client_uses_prompt_template_file() -> None:
    provider = _StubProvider(
        responses=['{"items":[{"type":"permission_boundary","question":"What is role boundary?","priority":"HIGH"}]}']
    )
    client = CloudModelClient(provider=provider)

    result = client.structured_invoke(
        prompt_name="missing_info_analyzer",
        input_data={"merged_text": "need export capability", "parsed_requirement": {}},
        schema=MissingInfoListSchema,
    )

    assert isinstance(result, dict)
    assert "items" in result
    assert provider.last_prompt is not None
    assert "Node Template (missing_info_analyzer)" in provider.last_prompt
    assert "Hard Constraints" in provider.last_prompt
