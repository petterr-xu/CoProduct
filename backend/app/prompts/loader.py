from __future__ import annotations

"""Prompt template loader and strict structured prompt composer."""

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel

_PROMPT_DIR = Path(__file__).resolve().parent
_PROMPT_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class PromptBuildResult:
    """Composed prompt with metadata for observability."""

    prompt_name: str
    prompt_text: str
    prompt_hash: str
    schema_name: str


def _schema_contract(schema: type) -> tuple[str, str]:
    if schema is list:
        return (
            "list",
            "Top-level response MUST be a JSON array. Return [] when there is no data.",
        )
    if schema is dict:
        return (
            "dict",
            "Top-level response MUST be a JSON object. Use {} when there is no data.",
        )
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        return (
            schema.__name__,
            (
                "Top-level response MUST be a JSON object that validates against the schema below.\n"
                "Use exact field names and valid enum values only.\n"
                f"JSON Schema: {schema_json}"
            ),
        )
    return (
        getattr(schema, "__name__", str(schema)),
        "Top-level response MUST be valid JSON.",
    )


def _validate_prompt_name(prompt_name: str) -> None:
    if not _PROMPT_NAME_PATTERN.match(prompt_name):
        raise RuntimeError(f"invalid prompt_name: {prompt_name}")


@lru_cache(maxsize=64)
def load_prompt_template(prompt_name: str) -> str:
    """Load prompt markdown template by node name."""
    _validate_prompt_name(prompt_name)
    prompt_path = _PROMPT_DIR / f"{prompt_name}.md"
    if not prompt_path.exists():
        raise RuntimeError(f"prompt template not found: {prompt_name}")
    text = prompt_path.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError(f"prompt template is empty: {prompt_name}")
    return text


def build_structured_prompt(*, prompt_name: str, input_data: dict[str, Any], schema: type) -> PromptBuildResult:
    """Compose a strict, schema-bound prompt from template + runtime payload."""
    template = load_prompt_template(prompt_name)
    schema_name, schema_contract = _schema_contract(schema)

    prompt_text = (
        "You are a strict backend workflow node.\n"
        "Follow the node instruction and output JSON only.\n\n"
        f"## Node Template ({prompt_name})\n"
        f"{template}\n\n"
        "## Schema Contract\n"
        f"{schema_contract}\n\n"
        "## Output Hard Rules\n"
        "- Output MUST be valid JSON only.\n"
        "- Do not output markdown, code fences, comments, or explanation text.\n"
        "- Do not rename fields.\n"
        "- Do not add unknown fields.\n"
        "- If uncertain, return a minimally valid JSON object/array that still follows schema.\n\n"
        "## Input Payload (JSON)\n"
        f"{json.dumps(input_data, ensure_ascii=False)}"
    )
    prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:12]
    return PromptBuildResult(
        prompt_name=prompt_name,
        prompt_text=prompt_text,
        prompt_hash=prompt_hash,
        schema_name=schema_name,
    )
