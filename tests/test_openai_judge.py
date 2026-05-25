"""OpenAIJudge tests with a stub client. No live API calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from medimage_eval.judges import JudgeAPIError, JudgeQuery, OpenAIJudge


@dataclass
class _Message:
    content: str


@dataclass
class _Choice:
    message: _Message


@dataclass
class _Response:
    choices: list[_Choice]


@dataclass
class _StubCompletions:
    response: _Response | Exception
    calls: list[dict[str, Any]] = field(default_factory=list)

    def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@dataclass
class _StubChat:
    completions: _StubCompletions


@dataclass
class _StubClient:
    chat: _StubChat


def _client_returning(text: str) -> _StubClient:
    return _StubClient(_StubChat(_StubCompletions(_Response([_Choice(_Message(text))]))))


def _client_raising(exc: Exception) -> _StubClient:
    return _StubClient(_StubChat(_StubCompletions(exc)))


def test_grade_returns_verdict_for_pass_label():
    stub = _client_returning('{"label": 1, "rationale": "matches"}')
    judge = OpenAIJudge(client=stub)
    verdict = judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))
    assert verdict.prompt_id == "q0"
    assert verdict.label == 1
    assert verdict.rationale == "matches"


def test_grade_uses_max_completion_tokens_not_max_tokens():
    """GPT-5+ requires max_completion_tokens. max_tokens is the legacy name."""
    stub = _client_returning('{"label": 0, "rationale": "x"}')
    judge = OpenAIJudge(client=stub)
    judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))
    call = stub.chat.completions.calls[0]
    assert "max_completion_tokens" in call
    assert "max_tokens" not in call


def test_grade_uses_structured_response_format():
    stub = _client_returning('{"label": 1, "rationale": "x"}')
    judge = OpenAIJudge(client=stub)
    judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))
    call = stub.chat.completions.calls[0]
    assert call["model"] == "gpt-5.4"
    rf = call["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["strict"] is True
    assert rf["json_schema"]["name"] == "grading_decision"


def test_grade_wraps_api_errors():
    stub = _client_raising(RuntimeError("rate limit"))
    judge = OpenAIJudge(client=stub)
    with pytest.raises(JudgeAPIError, match="openai judge call failed"):
        judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))


def test_grade_rejects_empty_choices():
    stub = _StubClient(_StubChat(_StubCompletions(_Response(choices=[]))))
    judge = OpenAIJudge(client=stub)
    with pytest.raises(JudgeAPIError, match="no choices"):
        judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))


def test_grade_rejects_empty_message_content():
    stub = _client_returning("")
    judge = OpenAIJudge(client=stub)
    with pytest.raises(JudgeAPIError, match="empty content"):
        judge.grade(JudgeQuery(prompt_id="q0", gold="g", candidate="c"))
