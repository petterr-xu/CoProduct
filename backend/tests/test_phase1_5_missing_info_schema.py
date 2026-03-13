from __future__ import annotations

from app.model_client.heuristic import HeuristicModelClient
from app.services.persistence_service import PersistenceService
from app.workflow.nodes.missing_info_analyzer import MissingInfoAnalyzerNode


class _InvalidMissingInfoClient:
    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type):  # noqa: ANN001, ARG002
        return {
            "items": [
                {
                    "missing_info_type": "permission",
                    "question_text": "权限边界是什么？",
                    "priority_level": "P0",
                }
            ]
        }


def test_missing_info_node_accepts_strict_schema_output() -> None:
    node = MissingInfoAnalyzerNode(HeuristicModelClient())
    result = node(
        {
            "parsed_requirement": {"actors": []},
            "normalized_request": {"merged_text": "需要导出活动报名信息"},
        }
    )
    assert isinstance(result["missing_info_items"], list)
    assert all({"type", "question", "priority"}.issubset(item.keys()) for item in result["missing_info_items"])


def test_missing_info_node_raises_model_schema_error_for_invalid_payload() -> None:
    node = MissingInfoAnalyzerNode(_InvalidMissingInfoClient())
    try:
        node(
            {
                "parsed_requirement": {},
                "normalized_request": {"merged_text": "需要导出活动报名信息"},
            }
        )
    except RuntimeError as exc:
        assert str(exc).startswith("MODEL_SCHEMA_ERROR:")
    else:
        raise AssertionError("Expected missing_info_analyzer to fail with MODEL_SCHEMA_ERROR")


def test_persistence_extracts_prefixed_schema_error_code() -> None:
    code = PersistenceService._error_code_from_message(
        status="FAILED",
        error_message="MODEL_SCHEMA_ERROR: missing_info_analyzer output invalid",
    )
    assert code == "MODEL_SCHEMA_ERROR"
