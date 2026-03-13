from __future__ import annotations

"""Language guard for strict structured-output locale enforcement."""

import re
from typing import Any

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

_NATURAL_TEXT_PATHS_BY_PROMPT: dict[str, list[str]] = {
    "requirement_parser": [
        "goal",
        "expected_output",
        "actors[*]",
        "business_objects[*]",
        "data_objects[*]",
        "constraints[*]",
        "uncertain_points[*]",
    ],
    "retrieval_planner": ["queries[*]"],
    "capability_judge": ["reason"],
    "missing_info_analyzer": ["items[*].question"],
    "risk_analyzer": ["items[*].description"],
    "impact_analyzer": ["items[*].reason"],
    "report_composer": [
        "summary",
        "capabilityJudgement.reason",
        "structuredDraft.goal",
        "structuredDraft.expected_output",
        "structuredDraft.actors[*]",
        "structuredDraft.business_objects[*]",
        "structuredDraft.data_objects[*]",
        "structuredDraft.constraints[*]",
        "structuredDraft.uncertain_points[*]",
        "missingInfoItems[*].question",
        "riskItems[*].description",
        "impactItems[*].reason",
        "nextSteps[*]",
    ],
}


def enforce_output_language(*, prompt_name: str, payload: Any, output_language: str, enforce: bool) -> None:
    """Fail closed when natural-language fields do not satisfy target language."""
    if not enforce:
        return
    if not _is_zh_cn(output_language):
        return

    path_specs = _NATURAL_TEXT_PATHS_BY_PROMPT.get(prompt_name, [])
    violations: list[str] = []
    for path_spec in path_specs:
        for actual_path, value in _iter_values_by_path(payload, path_spec):
            text = value.strip()
            if not text:
                continue
            if not _contains_cjk(text):
                violations.append(f"{actual_path}={_truncate(text)}")
                if len(violations) >= 5:
                    break
        if len(violations) >= 5:
            break

    if violations:
        detail = "; ".join(violations)
        raise RuntimeError(f"MODEL_LANGUAGE_ERROR: expected zh-CN output, violations: {detail}")


def _is_zh_cn(output_language: str) -> bool:
    normalized = (output_language or "").strip().lower().replace("_", "-")
    return normalized in {"zh", "zh-cn"}


def _contains_cjk(text: str) -> bool:
    return _CJK_RE.search(text) is not None


def _truncate(text: str, max_chars: int = 40) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}..."


def _iter_values_by_path(payload: Any, path_spec: str) -> list[tuple[str, str]]:
    tokens = [token for token in path_spec.split(".") if token]
    return _walk(payload, tokens, current_path="")


def _walk(node: Any, tokens: list[str], *, current_path: str) -> list[tuple[str, str]]:
    if not tokens:
        if isinstance(node, str):
            return [(current_path or "$", node)]
        return []

    token = tokens[0]
    rest = tokens[1:]

    if token.endswith("[*]"):
        key = token[:-3]
        if not isinstance(node, dict):
            return []
        value = node.get(key)
        if not isinstance(value, list):
            return []
        output: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            next_path = f"{current_path}.{key}[{index}]" if current_path else f"{key}[{index}]"
            output.extend(_walk(item, rest, current_path=next_path))
        return output

    if not isinstance(node, dict):
        return []
    next_node = node.get(token)
    next_path = f"{current_path}.{token}" if current_path else token
    return _walk(next_node, rest, current_path=next_path)

