"""Structured-output schema for judge decisions.

A judge always emits `{label: 0 or 1, rationale: str}`. This schema is used:

* As the JSON-schema constraint sent to the provider API (Anthropic
  `output_config.format` + OpenAI `response_format`) so the model returns
  parseable JSON without prefill tricks (prefills 400 on Claude Opus 4.7).
* As a lenient parser for free-text responses (with `parse_decision_text`)
  in case a provider returns text outside the schema constraint.
"""

from __future__ import annotations

import json
import re
from typing import Any

GRADING_DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "label": {"type": "integer", "enum": [0, 1]},
        "rationale": {"type": "string"},
    },
    "required": ["label", "rationale"],
    "additionalProperties": False,
}


class DecisionParseError(ValueError):
    """Raised when a judge response cannot be parsed into a GradingDecision."""


def parse_decision_text(text: str) -> tuple[int, str]:
    """Parse a judge response into (label, rationale).

    Accepts either a strict JSON object or a JSON object embedded in text
    (e.g. wrapped in a Markdown code fence). Raises `DecisionParseError`
    on anything that does not yield `{label: 0|1, rationale: str}`.
    """
    if not text or not text.strip():
        raise DecisionParseError("empty judge response")

    obj = _extract_json_object(text)
    if "label" not in obj or "rationale" not in obj:
        raise DecisionParseError(f"missing required fields in judge response: {obj!r}")

    label = obj["label"]
    if isinstance(label, bool) or not isinstance(label, int) or label not in (0, 1):
        raise DecisionParseError(f"label must be 0 or 1, got {label!r}")

    rationale = obj["rationale"]
    if not isinstance(rationale, str):
        raise DecisionParseError(f"rationale must be a string, got {type(rationale).__name__}")

    return label, rationale


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json_object(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of `text`. Tolerates fences and surrounding prose."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence_match = _JSON_FENCE_RE.search(text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError as exc:
            raise DecisionParseError(f"fenced JSON failed to parse: {exc}") from exc

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise DecisionParseError(f"object slice failed to parse: {exc}") from exc

    raise DecisionParseError(f"no JSON object found in judge response: {text[:120]!r}")
