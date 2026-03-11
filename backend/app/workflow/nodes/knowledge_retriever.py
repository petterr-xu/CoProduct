from __future__ import annotations

from app.rag import HybridSearcher
from app.workflow.state import PreReviewState


class KnowledgeRetrieverNode:
    """Retrieve candidates with fixed M2 hybrid strategy.

    Flow: FTS top20 + vector top20 + merge dedupe + global rerank.
    """

    def __init__(self, searcher: HybridSearcher) -> None:
        self.searcher = searcher

    def __call__(self, state: PreReviewState) -> dict:
        retrieval_plan = state.get("retrieval_plan", {})
        queries = retrieval_plan.get("queries") or [state.get("normalized_request", {}).get("merged_text", "")]
        candidates = self.searcher.search(
            queries=[str(query) for query in queries if str(query).strip()],
            source_filters=retrieval_plan.get("source_filters", {}),
            module_tags=retrieval_plan.get("module_tags", []),
            top_k=20,
        )
        return {"retrieved_candidates": candidates}
