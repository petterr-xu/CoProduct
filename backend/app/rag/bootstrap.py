from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.model_client.base import ModelClient
from app.models import KnowledgeChunkModel, KnowledgeDocumentModel
from app.rag.search import chunk_document


BUILTIN_DOCS: list[dict] = [
    {
        "doc_title": "导出 API 说明",
        "source_type": "api_doc",
        "trust_level": "HIGH",
        "module_tag": "export_service",
        "content": (
            "系统支持按活动导出报名数据，导出任务采用异步执行。"
            "导出接口支持 CSV 与 XLSX，最大建议 10 万行。"
            "超大批量需走分片任务并在后台通知完成。"
        ),
    },
    {
        "doc_title": "权限规范",
        "source_type": "constraint_doc",
        "trust_level": "HIGH",
        "module_tag": "permission",
        "content": (
            "导出手机号等敏感字段必须具备审批后的角色权限。"
            "所有导出行为需记录审计日志，包含操作者与时间范围。"
            "普通运营角色默认仅可导出脱敏字段。"
        ),
    },
    {
        "doc_title": "报名业务说明",
        "source_type": "product_doc",
        "trust_level": "MEDIUM",
        "module_tag": "registration",
        "content": (
            "报名模块提供活动维度筛选能力，支持按时间、渠道、状态过滤。"
            "查询结果可分页展示，导出时建议校验权限与导出上限。"
        ),
    },
]


def ensure_builtin_knowledge(session_factory: sessionmaker, model_client: ModelClient) -> None:
    """Seed minimal knowledge corpus for M2 retrieval if DB is empty."""
    with session_factory() as db:
        existing = db.execute(select(func.count(KnowledgeChunkModel.id))).scalar_one()
        if existing and existing > 0:
            return

        for document in BUILTIN_DOCS:
            doc = KnowledgeDocumentModel(
                doc_title=document["doc_title"],
                source_type=document["source_type"],
                trust_level=document["trust_level"],
                module_tag=document.get("module_tag"),
                content=document["content"],
            )
            db.add(doc)
            db.flush()

            chunks = chunk_document(document["content"], target_size=420)
            embeddings = model_client.embed_texts(chunks) if chunks else []
            for index, chunk in enumerate(chunks):
                embedding = embeddings[index] if index < len(embeddings) else []
                db.add(
                    KnowledgeChunkModel(
                        doc_id=doc.id,
                        chunk_text=chunk,
                        section_path=f"section_{index + 1}",
                        embedding_json=json.dumps(embedding),
                        tsv=chunk,
                    )
                )

        db.commit()

