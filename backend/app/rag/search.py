from __future__ import annotations

import json
import math
import re

from sqlalchemy import Select, select
from sqlalchemy.orm import sessionmaker

from app.model_client.base import ModelClient
from app.models import KnowledgeChunkModel, KnowledgeDocumentModel


def _tokenize(text: str) -> list[str]:
    parts = re.split(r"[\s,.;:!?，。；：！？、/\\()（）\[\]{}<>\"'`~\-_|]+", text.lower())
    tokens = [part for part in parts if part]

    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text.lower())
    tokens.extend(cjk_chars)
    if len(cjk_chars) >= 2:
        tokens.extend("".join(cjk_chars[index : index + 2]) for index in range(len(cjk_chars) - 1))
    return tokens


def _cosine(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a * a for a in v1))
    n2 = math.sqrt(sum(a * a for a in v2))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


class HybridSearcher:
    """Hybrid searcher with fixed M2 flow: FTS + vector + merge + rerank."""

    def __init__(self, session_factory: sessionmaker, model_client: ModelClient) -> None:
        self.session_factory = session_factory
        self.model_client = model_client

    def search(
        self,
        *,
        queries: list[str],
        source_filters: dict | None = None,
        module_tags: list[str] | None = None,
        top_k: int = 20,
    ) -> list[dict]:
        filters = source_filters or {}
        merged: dict[str, dict] = {}

        for query in queries:
            fts_hits, vector_hits = self._search_single(
                query=query,
                source_filters=filters,
                module_tags=module_tags or [],
                top_k=top_k,
            )
            for item in fts_hits + vector_hits:
                chunk_id = item["chunk_id"]
                existing = merged.get(chunk_id)
                if existing is None or item["relevance_score"] > existing["relevance_score"]:
                    merged[chunk_id] = item

        # Global rerank over merged pool.
        ranked = list(merged.values())
        if ranked:
            snippets = [item["snippet"] for item in ranked]
            rerank_indices = self.model_client.rerank(" ".join(queries), snippets)
            ordered = [ranked[index] for index in rerank_indices if 0 <= index < len(ranked)]
        else:
            ordered = []
        return ordered[:top_k]

    def _search_single(
        self,
        *,
        query: str,
        source_filters: dict,
        module_tags: list[str],
        top_k: int,
    ) -> tuple[list[dict], list[dict]]:
        rows = self._load_chunks(source_filters=source_filters, module_tags=module_tags)
        if not rows:
            return [], []

        query_tokens = set(_tokenize(query))
        query_vector = self.model_client.embed_texts([query])[0]
        chunk_texts = [row["chunk_text"] for row in rows]
        generated_vectors = self.model_client.embed_texts(chunk_texts)

        fts_scored: list[tuple[int, float]] = []
        vector_scored: list[tuple[int, float]] = []
        for index, row in enumerate(rows):
            tokens = set(_tokenize(row["chunk_text"]))
            overlap = len(tokens.intersection(query_tokens))
            if overlap > 0:
                fts_scored.append((index, float(overlap)))
            chunk_vector = row.get("embedding") or generated_vectors[index]
            vec_score = _cosine(query_vector, chunk_vector)
            vector_scored.append((index, vec_score))

        top_fts = sorted(fts_scored, key=lambda item: item[1], reverse=True)[:20]
        top_vector = sorted(vector_scored, key=lambda item: item[1], reverse=True)[:20]

        fts_hits = [self._build_hit(rows[index], score=score, stage="fts") for index, score in top_fts]
        vector_hits = [self._build_hit(rows[index], score=score, stage="vector") for index, score in top_vector]
        return fts_hits[:top_k], vector_hits[:top_k]

    def _load_chunks(self, *, source_filters: dict, module_tags: list[str]) -> list[dict]:
        with self.session_factory() as db:
            stmt: Select[tuple[KnowledgeChunkModel, KnowledgeDocumentModel]] = (
                select(KnowledgeChunkModel, KnowledgeDocumentModel)
                .join(KnowledgeDocumentModel, KnowledgeChunkModel.doc_id == KnowledgeDocumentModel.id)
            )

            module_hint = source_filters.get("module_hint")
            if module_hint:
                stmt = stmt.where(KnowledgeDocumentModel.module_tag == str(module_hint))

            rows = db.execute(stmt).all()
            result = []
            for chunk, doc in rows:
                result.append(
                    {
                        "doc_id": doc.id,
                        "doc_title": doc.doc_title,
                        "source_type": doc.source_type,
                        "trust_level": doc.trust_level,
                        "chunk_id": chunk.id,
                        "chunk_text": chunk.chunk_text,
                        "embedding": self._parse_embedding(chunk.embedding_json),
                    }
                )
            return result

    @staticmethod
    def _parse_embedding(payload: str | None) -> list[float] | None:
        if not payload:
            return None
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, list):
                return [float(item) for item in parsed]
        except (TypeError, ValueError):
            return None
        return None

    @staticmethod
    def _build_hit(row: dict, *, score: float, stage: str) -> dict:
        source_type = str(row["source_type"] or "product_doc")
        if source_type not in {"product_doc", "api_doc", "constraint_doc", "case"}:
            source_type = "product_doc"
        trust_level = str(row["trust_level"] or "MEDIUM").upper()
        if trust_level not in {"HIGH", "MEDIUM", "LOW"}:
            trust_level = "MEDIUM"

        return {
            "doc_id": row["doc_id"],
            "doc_title": row["doc_title"],
            "chunk_id": row["chunk_id"],
            "snippet": row["chunk_text"],
            "source_type": source_type,
            "relevance_score": round(float(score), 4),
            "trust_level": trust_level,
            "retrieval_stage": stage,
        }


def chunk_document(content: str, *, target_size: int = 400) -> list[str]:
    """Simple chunker for MVP seeding and local retrieval."""
    text = content.strip()
    if not text:
        return []
    if len(text) <= target_size:
        return [text]

    sentences = re.split(r"(?<=[。！？.!?])", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(current) + len(sentence) <= target_size:
            current += sentence
        else:
            if current:
                chunks.append(current.strip())
            current = sentence
    if current:
        chunks.append(current.strip())

    # dedupe while keeping order
    ordered_unique = list(dict.fromkeys(chunks))
    return ordered_unique
