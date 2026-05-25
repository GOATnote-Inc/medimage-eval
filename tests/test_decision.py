"""Tests for the lenient decision parser."""

from __future__ import annotations

import pytest

from medimage_eval.judges.decision import DecisionParseError, parse_decision_text


def test_strict_json_parses():
    label, rationale = parse_decision_text('{"label": 1, "rationale": "good"}')
    assert label == 1
    assert rationale == "good"


def test_fenced_json_parses():
    text = 'Here is my decision:\n```json\n{"label": 0, "rationale": "missed bleed"}\n```'
    label, rationale = parse_decision_text(text)
    assert label == 0
    assert rationale == "missed bleed"


def test_object_embedded_in_prose_parses():
    text = 'Sure thing. {"label": 1, "rationale": "matches gold"} done.'
    label, rationale = parse_decision_text(text)
    assert label == 1
    assert rationale == "matches gold"


def test_empty_response_rejected():
    with pytest.raises(DecisionParseError, match="empty"):
        parse_decision_text("")


def test_missing_label_rejected():
    with pytest.raises(DecisionParseError, match="missing required"):
        parse_decision_text('{"rationale": "ok"}')


def test_label_must_be_zero_or_one():
    with pytest.raises(DecisionParseError, match="label must be 0 or 1"):
        parse_decision_text('{"label": 2, "rationale": "x"}')


def test_label_true_is_rejected():
    """Bool is a subclass of int in Python; reject it explicitly."""
    with pytest.raises(DecisionParseError, match="label must be 0 or 1"):
        parse_decision_text('{"label": true, "rationale": "x"}')


def test_rationale_must_be_string():
    with pytest.raises(DecisionParseError, match="rationale must be a string"):
        parse_decision_text('{"label": 1, "rationale": 42}')


def test_garbage_input_rejected():
    with pytest.raises(DecisionParseError):
        parse_decision_text("totally not json at all")
