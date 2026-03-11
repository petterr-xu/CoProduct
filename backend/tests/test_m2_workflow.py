from __future__ import annotations

from app.model_client.heuristic import HeuristicModelClient
from app.workflow.nodes.capability_judge import CapabilityJudgeNode


def test_capability_judge_blocks_supported_without_high_quality_evidence() -> None:
    node = CapabilityJudgeNode(HeuristicModelClient())

    state = {
        "evidence_pack": [
            {
                "doc_id": "doc_1",
                "doc_title": "弱证据",
                "chunk_id": "chunk_1",
                "snippet": "相关性一般",
                "source_type": "case",
                "relevance_score": 0.8,
                "trust_level": "MEDIUM",
            }
        ],
        "parsed_requirement": {"uncertain_points": []},
    }

    result = node(state)
    assert result["capability_judgement"]["status"] != "SUPPORTED"


def test_capability_judge_allows_supported_with_sufficient_high_quality_evidence() -> None:
    node = CapabilityJudgeNode(HeuristicModelClient())

    state = {
        "evidence_pack": [
            {
                "doc_id": "doc_1",
                "doc_title": "导出 API",
                "chunk_id": "chunk_1",
                "snippet": "系统支持导出",
                "source_type": "api_doc",
                "relevance_score": 0.91,
                "trust_level": "HIGH",
            },
            {
                "doc_id": "doc_2",
                "doc_title": "权限规范",
                "chunk_id": "chunk_2",
                "snippet": "敏感字段需权限审批",
                "source_type": "constraint_doc",
                "relevance_score": 0.88,
                "trust_level": "HIGH",
            },
        ],
        "parsed_requirement": {"uncertain_points": []},
    }

    result = node(state)
    assert result["capability_judgement"]["status"] == "SUPPORTED"
    assert result["capability_judgement"]["confidence"] in {"high", "medium", "low"}

