"""RAG utilities."""

from app.rag.bootstrap import ensure_builtin_knowledge
from app.rag.search import HybridSearcher

__all__ = ["HybridSearcher", "ensure_builtin_knowledge"]
