"""AnthropicJudge tests with a stub client. No live API calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from medimage_eval.judges import AnthropicJudge, JudgeAPIError, JudgeQuery


@dataclass
class _Block:
    type: str
    text: str = ""


@dataclass
class _Response:
    content: list[_Block] = field(default_factory=list)
    stop_reason: str = "end_turn"


@dataclass
class _StubMessages:
    response: _Response | Exception
    calls: list[dict[str, Any]] = field(default_factory=list)

    def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@dataclass
class _StubClient:
    messages: _StubMessages


def _client_returning(text: str, stop_reason: str = "end_turn") -> _StubClient:
    return _StubClient(
        _StubMessages(_Response(content=[_Block("text", text)], stop_reason=stop_reason))
    )


def _client_raising(exc: Exception) -> _StubClient:
    return _StubClient(_StubMessages(exc))


def test_grade_returns_verdict_for_pass_label():
    stub = _client_returning('{"label": 1, "rationale": "matches gold report"}')
    judge = AnthropicJudge(client=stub)
    query = JudgeQuery(prompt_id="q0", gold="GOLD TEXT", candidate="CAND TEXT")
    verdict = judge.grade(query)
    assert verdict.prompt_id == "q0"
    assert verdict.label == 1
    assert verdict.rationale == "matches gold report"
    assert "matches gold report" in verdict.raw


def test_grade_passes_default_model_and_caching():
    stub = _client_returning('{"label": 0, "rationale": "missed bleed"}')
    judge = AnthropicJudge(client=stub)
    judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))
    call = stub.messages.calls[0]
    assert call["model"] == "claude-opus-4-7"
    # Cache control marker on the system prompt — required for prompt caching.
    system = call["system"]
    assert isinstance(system, list) and len(system) == 1
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    # No sampling params — they 400 on Opus 4.7.
    assert "temperature" not in call
    assert "top_p" not in call
    assert "top_k" not in call
    # No budget_tokens — also 400 on Opus 4.7.
    assert "thinking" not in call or call["thinking"].get("type") != "enabled"
    # Structured output via output_config.format, not prefill.
    assert call["output_config"]["format"]["type"] == "json_schema"


def test_grade_passes_user_payload_with_gold_and_candidate():
    stub = _client_returning('{"label": 1, "rationale": "ok"}')
    judge = AnthropicJudge(client=stub)
    judge.grade(
        JudgeQuery(
            prompt_id="q0", gold="GOLD-TOKEN", candidate="CAND-TOKEN", instructions="be strict"
        )
    )
    user_content = stub.messages.calls[0]["messages"][0]["content"]
    assert "GOLD-TOKEN" in user_content
    assert "CAND-TOKEN" in user_content
    assert "be strict" in user_content


def test_grade_raises_on_refusal():
    stub = _client_returning('{"label": 0, "rationale": "ok"}', stop_reason="refusal")
    judge = AnthropicJudge(client=stub)
    with pytest.raises(JudgeAPIError, match="refused"):
        judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))


def test_grade_wraps_api_errors():
    stub = _client_raising(RuntimeError("connection reset"))
    judge = AnthropicJudge(client=stub)
    with pytest.raises(JudgeAPIError, match="anthropic judge call failed"):
        judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))


def test_grade_raises_when_response_has_no_text_block():
    stub = _StubClient(_StubMessages(_Response(content=[], stop_reason="end_turn")))
    judge = AnthropicJudge(client=stub)
    with pytest.raises(JudgeAPIError, match="no content"):
        judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))


def test_empty_model_id_rejected():
    with pytest.raises(ValueError, match="model_id"):
        AnthropicJudge(model_id="", client=_client_returning("{}"))


def test_handles_fenced_json_response():
    stub = _client_returning('```json\n{"label": 0, "rationale": "miss"}\n```')
    judge = AnthropicJudge(client=stub)
    verdict = judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))
    assert verdict.label == 0
    assert verdict.rationale == "miss"
