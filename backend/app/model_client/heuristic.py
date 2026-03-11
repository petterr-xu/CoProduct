from __future__ import annotations

import hashlib
import math
import re
import time
from typing import Any

from pydantic import BaseModel

from app.core.logging import log_event


def _tokenize(text: str) -> list[str]:
    lowered = text.lower()
    parts = re.split(r"[\s,.;:!?，。；：！？、/\\()（）\[\]{}<>\"'`~\-_|]+", lowered)
    tokens = [part for part in parts if part]

    cjk_chars = re.findall(r"[\u4e00-\u9fff]", lowered)
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


class HeuristicModelClient:
    """Deterministic model client for local/dev environments.

    It keeps node contracts stable without requiring external LLM providers.
    """

    def __init__(self, embedding_dim: int = 64) -> None:
        self.embedding_dim = embedding_dim

    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type) -> Any:
        start = time.perf_counter()
        payload: Any

        if prompt_name == "requirement_parser":
            payload = self._build_requirement(input_data.get("merged_text", ""))
        elif prompt_name == "retrieval_planner":
            payload = self._build_retrieval_plan(
                requirement_text=input_data.get("requirement_text", ""),
                parsed_requirement=input_data.get("parsed_requirement", {}),
                business_domain=input_data.get("business_domain"),
                module_hint=input_data.get("module_hint"),
            )
        elif prompt_name == "capability_judge":
            payload = self._build_capability(
                uncertain_points=input_data.get("uncertain_points", []),
                evidence_pack=input_data.get("evidence_pack", []),
            )
        elif prompt_name == "missing_info_analyzer":
            payload = self._build_missing_info(
                parsed_requirement=input_data.get("parsed_requirement", {}),
                merged_text=input_data.get("merged_text", ""),
            )
        elif prompt_name == "risk_analyzer":
            payload = self._build_risks(input_data.get("merged_text", ""))
        elif prompt_name == "impact_analyzer":
            payload = self._build_impacts(
                parsed_requirement=input_data.get("parsed_requirement", {}),
                module_hint=input_data.get("module_hint"),
            )
        elif prompt_name == "report_composer":
            payload = self._build_report(
                parsed_requirement=input_data.get("parsed_requirement", {}),
                capability=input_data.get("capability_judgement", {}),
                evidence=input_data.get("evidence_pack", []),
                missing_info=input_data.get("missing_info_items", []),
                risks=input_data.get("risk_items", []),
                impacts=input_data.get("impact_items", []),
            )
        else:
            raise ValueError(f"unsupported prompt_name: {prompt_name}")

        validated = self._validate_with_schema(payload, schema)
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_event(
            "model_structured_invoke",
            prompt_name=prompt_name,
            latency_ms=latency_ms,
            token_input_estimate=len(str(input_data)),
            token_output_estimate=len(str(validated)),
            cost_estimate=0.0,
            provider="heuristic",
        )
        return validated

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        start = time.perf_counter()
        vectors = [self._embed_text(text) for text in texts]
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_event(
            "model_embed_texts",
            latency_ms=latency_ms,
            text_count=len(texts),
            token_input_estimate=sum(len(text) for text in texts),
            cost_estimate=0.0,
            provider="heuristic",
        )
        return vectors

    def rerank(self, query: str, candidates: list[str]) -> list[int]:
        start = time.perf_counter()
        query_tokens = set(_tokenize(query))
        scored: list[tuple[int, float]] = []

        for index, candidate in enumerate(candidates):
            candidate_tokens = set(_tokenize(candidate))
            lexical_overlap = len(query_tokens.intersection(candidate_tokens))

            # Blend lexical overlap and embedding similarity for deterministic rerank.
            qv = self._embed_text(query)
            cv = self._embed_text(candidate)
            score = lexical_overlap + _cosine(qv, cv)
            scored.append((index, score))

        ranked_indices = [index for index, _ in sorted(scored, key=lambda item: item[1], reverse=True)]
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_event(
            "model_rerank",
            latency_ms=latency_ms,
            candidate_count=len(candidates),
            token_input_estimate=len(query) + sum(len(text) for text in candidates),
            cost_estimate=0.0,
            provider="heuristic",
        )
        return ranked_indices

    def _validate_with_schema(self, payload: Any, schema: type) -> Any:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema.model_validate(payload).model_dump()
        return payload

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.embedding_dim
        tokens = _tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:2], "big") % self.embedding_dim
            vector[slot] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _build_requirement(self, merged_text: str) -> dict:
        actors: set[str] = set()
        business_objects: set[str] = set()
        data_objects: set[str] = set()
        constraints: set[str] = set()
        uncertain_points: set[str] = set()

        goal = ""
        expected_output = ""

        if "运营" in merged_text:
            actors.add("运营")
        if "产品" in merged_text:
            actors.add("产品")
        if "客服" in merged_text:
            actors.add("客服")
        if "活动" in merged_text:
            business_objects.add("活动")
        if "报名" in merged_text:
            business_objects.add("报名")
            data_objects.add("报名记录")
        if "导出" in merged_text:
            goal = "支持导出能力"
            expected_output = "导出文件"
            business_objects.add("导出任务")
        if "权限" in merged_text or "角色" in merged_text:
            constraints.add("角色权限边界")
        if "审计" in merged_text:
            constraints.add("导出审计日志")

        if not goal:
            uncertain_points.add("业务目标不明确")
        if "权限" not in merged_text and "角色" not in merged_text:
            uncertain_points.add("权限边界不明确")
        has_time_requirement = any(token in merged_text for token in ("时间", "时效", "小时", "天", "周", "月", "分钟"))
        if not has_time_requirement:
            uncertain_points.add("时间要求不明确")

        return {
            "goal": goal,
            "actors": sorted(actors),
            "business_objects": sorted(business_objects),
            "data_objects": sorted(data_objects),
            "constraints": sorted(constraints),
            "expected_output": expected_output,
            "uncertain_points": sorted(uncertain_points),
        }

    def _build_retrieval_plan(
        self,
        requirement_text: str,
        parsed_requirement: dict,
        business_domain: str | None,
        module_hint: str | None,
    ) -> dict:
        base = requirement_text.strip() or "需求"
        queries = [f"{base} 能力", f"{base} API", f"{base} 限制 风险"]

        if parsed_requirement.get("business_objects"):
            query = f"{base} {' '.join(parsed_requirement['business_objects'])}"
            queries.append(query)
        if parsed_requirement.get("uncertain_points"):
            queries.append(f"{base} 相似案例")

        return {
            "queries": queries[:5],
            "source_filters": {
                "business_domain": business_domain,
                "module_hint": module_hint,
            },
            "module_tags": parsed_requirement.get("business_objects", []),
        }

    def _build_capability(self, uncertain_points: list[str], evidence_pack: list[dict]) -> dict:
        high_quality_count = sum(
            1
            for item in evidence_pack
            if str(item.get("trust_level", "")).upper() == "HIGH" and float(item.get("relevance_score", 0.0)) >= 0.75
        )
        if uncertain_points:
            status = "NEED_MORE_INFO"
            reason = "需求关键信息仍存在缺口。"
        elif not evidence_pack:
            status = "NOT_SUPPORTED"
            reason = "未检索到可支撑结论的证据。"
        elif high_quality_count >= 2:
            status = "SUPPORTED"
            reason = "已有充分高质量证据支持能力实现。"
        elif high_quality_count >= 1:
            status = "PARTIALLY_SUPPORTED"
            reason = "存在部分高质量证据，但约束条件仍需补充。"
        else:
            status = "NOT_SUPPORTED"
            reason = "证据相关性或可信度不足。"

        confidence = "low"
        if high_quality_count >= 2:
            confidence = "high"
        elif high_quality_count == 1:
            confidence = "medium"

        return {
            "status": status,
            "reason": reason,
            "confidence": confidence,
            "evidence_refs": [item.get("chunk_id", "") for item in evidence_pack if item.get("chunk_id")],
        }

    def _build_missing_info(self, parsed_requirement: dict, merged_text: str) -> list[dict]:
        items: list[dict] = []
        if not parsed_requirement.get("actors"):
            items.append({"type": "target_user", "question": "目标用户是谁？", "priority": "HIGH"})
        if "权限" not in merged_text and "角色" not in merged_text:
            items.append({"type": "permission_boundary", "question": "不同角色权限边界是什么？", "priority": "HIGH"})
        has_time_requirement = any(token in merged_text for token in ("时间", "时效", "小时", "天", "周", "月", "分钟"))
        if not has_time_requirement:
            items.append({"type": "time_requirement", "question": "是否有明确时效要求？", "priority": "MEDIUM"})
        if "性能" not in merged_text and "量级" not in merged_text:
            items.append({"type": "performance_requirement", "question": "数据规模和性能目标是什么？", "priority": "MEDIUM"})
        return items

    def _build_risks(self, merged_text: str) -> list[dict]:
        risks: list[dict] = []
        if "导出" in merged_text and ("手机号" in merged_text or "用户" in merged_text):
            risks.append(
                {
                    "type": "security",
                    "description": "导出涉及敏感数据，需权限控制和审计。",
                    "level": "HIGH",
                }
            )
        if "批量" in merged_text:
            risks.append(
                {
                    "type": "performance",
                    "description": "批量任务可能带来性能和资源竞争风险。",
                    "level": "MEDIUM",
                }
            )
        return risks

    def _build_impacts(self, parsed_requirement: dict, module_hint: str | None) -> list[dict]:
        impacts: list[dict] = []
        if module_hint:
            impacts.append({"module": module_hint, "reason": "模块提示命中"})
        for business_object in parsed_requirement.get("business_objects", []):
            if business_object == "导出任务":
                impacts.append({"module": "export_service", "reason": "导出能力相关"})
            if business_object == "报名":
                impacts.append({"module": "registration", "reason": "业务对象命中"})
        return impacts

    def _build_report(
        self,
        parsed_requirement: dict,
        capability: dict,
        evidence: list[dict],
        missing_info: list[dict],
        risks: list[dict],
        impacts: list[dict],
    ) -> dict:
        summary = (
            f"目标：{parsed_requirement.get('goal') or '待补充'}；"
            f"能力判断：{capability.get('status', 'NEED_MORE_INFO')}；"
            f"证据数：{len(evidence)}；"
            f"待补充项：{len(missing_info)}。"
        )
        return {
            "summary": summary,
            "capabilityJudgement": capability,
            "structuredDraft": parsed_requirement,
            "evidence": evidence,
            "missingInfoItems": missing_info,
            "riskItems": risks,
            "impactItems": impacts,
            "nextSteps": [
                "优先补齐高优先级缺失信息。",
                "对高风险点补充约束并评估实施方案。",
            ],
        }
