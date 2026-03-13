from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel


class StructuredOutputError(RuntimeError):
    """Raised when the model output cannot be recovered into the target schema."""


@dataclass
class StructuredOutputAttempt:
    raw_text: str
    parsed_payload: Any
    validated_payload: Any


def parse_json_payload(raw_text: str) -> Any:
    """Parse JSON payload from a model response with lightweight recovery."""
    text = raw_text.strip()
    if not text:
        raise StructuredOutputError("empty model output")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting a JSON block from markdown-like wrappers.
    first_object = text.find("{")
    last_object = text.rfind("}")
    if first_object != -1 and last_object != -1 and last_object > first_object:
        try:
            return json.loads(text[first_object : last_object + 1])
        except json.JSONDecodeError:
            pass

    first_array = text.find("[")
    last_array = text.rfind("]")
    if first_array != -1 and last_array != -1 and last_array > first_array:
        try:
            return json.loads(text[first_array : last_array + 1])
        except json.JSONDecodeError:
            pass

    raise StructuredOutputError("model output is not valid json")


def validate_payload(payload: Any, schema: type) -> Any:
    """Validate payload against pydantic model or builtin list/dict target."""
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return schema.model_validate(payload).model_dump()
    if schema is list:
        if not isinstance(payload, list):
            raise StructuredOutputError("expected a JSON array")
        return payload
    if schema is dict:
        if not isinstance(payload, dict):
            raise StructuredOutputError("expected a JSON object")
        return payload
    return payload


def repair_prompt(*, prompt_name: str, raw_text: str, error_message: str, schema: type) -> str:
    """Build a deterministic repair prompt to coerce output into strict JSON."""
    target = "JSON object"
    if schema is list:
        target = "JSON array"
    elif schema is dict:
        target = "JSON object"
    elif isinstance(schema, type) and issubclass(schema, BaseModel):
        target = f"JSON object that matches schema {schema.__name__}"

    return (
        "You are a strict JSON formatter.\n"
        f"Task: repair output for `{prompt_name}`.\n"
        f"Requirement: return ONLY a {target}. No markdown, no explanation.\n"
        f"Validation error: {error_message}\n"
        "Original output:\n"
        f"{raw_text}\n"
    )


def invoke_with_validation(
    *,
    prompt_name: str,
    schema: type,
    invoke_text: Callable[[str], str],
    base_prompt: str,
    max_retries: int,
) -> StructuredOutputAttempt:
    """Generate, validate, and repair structured output with bounded retries."""
    prompt = base_prompt
    last_error = "unknown"

    for _ in range(max_retries + 1):
        raw_text = invoke_text(prompt)
        try:
            parsed = parse_json_payload(raw_text)
            validated = validate_payload(parsed, schema)
            return StructuredOutputAttempt(raw_text=raw_text, parsed_payload=parsed, validated_payload=validated)
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            prompt = repair_prompt(prompt_name=prompt_name, raw_text=raw_text, error_message=last_error, schema=schema)

    raise StructuredOutputError(f"failed to produce valid structured output: {last_error}")

