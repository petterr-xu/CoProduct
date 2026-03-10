from __future__ import annotations

from app.workflow.state import PreReviewState


class KnowledgeRetrieverNode:
    """M1 placeholder retriever.

    Later this node will call rag.search (FTS + pgvector).
    """

    def __call__(self, state: PreReviewState) -> dict:
        merged_text = state["normalized_request"].get("merged_text", "")
        module_hint = state["normalized_request"].get("module_hint") or "general"

        candidates: list[dict] = []
        if "导出" in merged_text:
            candidates.append(
                {
                    "doc_id": "doc_api_export_001",
                    "doc_title": "导出 API 说明",
                    "chunk_id": "chunk_01",
                    "snippet": "系统支持按活动导出报名数据，建议异步任务执行。",
                    "source_type": "api_doc",
                    "relevance_score": 0.91,
                    "trust_level": "HIGH",
                    "module_tag": module_hint,
                }
            )
        if "权限" in merged_text or "角色" in merged_text:
            candidates.append(
                {
                    "doc_id": "doc_permission_001",
                    "doc_title": "权限规范",
                    "chunk_id": "chunk_04",
                    "snippet": "导出手机号等敏感字段需要角色权限和审计记录。",
                    "source_type": "constraint_doc",
                    "relevance_score": 0.87,
                    "trust_level": "HIGH",
                    "module_tag": "permission",
                }
            )
        if not candidates:
            candidates.append(
                {
                    "doc_id": "doc_case_001",
                    "doc_title": "历史需求案例",
                    "chunk_id": "chunk_12",
                    "snippet": "历史需求与当前场景相似，但关键信息缺失。",
                    "source_type": "case",
                    "relevance_score": 0.56,
                    "trust_level": "MEDIUM",
                    "module_tag": module_hint,
                }
            )

        return {"retrieved_candidates": candidates}

