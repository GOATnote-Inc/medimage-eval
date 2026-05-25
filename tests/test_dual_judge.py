"""Tests for the dual-judge runner.

These tests use a deterministic in-memory judge so we can verify aggregation,
kappa flooring, and reward-rejection without live API calls.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from medimage_eval.judges import (
    DualJudge,
    JudgeQuery,
    JudgeVerdict,
)


@dataclass
class ScriptedJudge:
    """A judge whose verdict per prompt_id is fixed up front."""

    model_id: str
    script: dict[str, int]

    def grade(self, query: JudgeQuery) -> JudgeVerdict:
        return JudgeVerdict(
            prompt_id=query.prompt_id,
            label=self.script[query.prompt_id],
            rationale="scripted",
            raw="scripted",
        )


def _queries(ids: list[str]) -> list[JudgeQuery]:
    return [JudgeQuery(prompt_id=i, gold="gold", candidate="cand") for i in ids]


def test_perfect_agreement_accepted():
    p = ScriptedJudge("primary", {f"q{i}": 1 for i in range(10)})
    s = ScriptedJudge("secondary", {f"q{i}": 1 for i in range(10)})
    dj = DualJudge(p, s, kappa_floor=0.6)
    result = dj.evaluate(_queries([f"q{i}" for i in range(10)]))
    assert result.n_items == 10
    assert result.primary_pass_rate == 1.0
    assert result.secondary_pass_rate == 1.0
    assert result.agreement_rate == 1.0
    # All same-label: κ is degenerate (numerator and denominator both 0). Implementation
    # returns 1.0 in the all-agree, observed-equals-expected-equals-1 corner.
    assert result.kappa == pytest.approx(1.0)
    assert result.reward_signal_accepted is True


def test_strong_disagreement_rejected():
    # 10 items; judges agree on 4 of them, with mixed labels — κ below floor.
    p_script = {f"q{i}": (1 if i < 5 else 0) for i in range(10)}
    s_script = {f"q{i}": (1 if i in {0, 1, 8, 9} else 0) for i in range(10)}
    p = ScriptedJudge("primary", p_script)
    s = ScriptedJudge("secondary", s_script)
    dj = DualJudge(p, s, kappa_floor=0.6)
    result = dj.evaluate(_queries([f"q{i}" for i in range(10)]))
    assert result.kappa < 0.6
    assert result.reward_signal_accepted is False


def test_distinct_models_required():
    j = ScriptedJudge("same-model", {"q0": 1})
    with pytest.raises(ValueError, match="distinct"):
        DualJudge(j, j)


def test_empty_batch_handled():
    p = ScriptedJudge("primary", {})
    s = ScriptedJudge("secondary", {})
    dj = DualJudge(p, s, kappa_floor=0.6)
    result = dj.evaluate([])
    assert result.n_items == 0
    assert result.reward_signal_accepted is False


def test_mismatched_prompt_id_raises():
    class WrongIdJudge:
        model_id = "buggy"

        def grade(self, query: JudgeQuery) -> JudgeVerdict:
            return JudgeVerdict(prompt_id="not-the-right-id", label=1)

    s = ScriptedJudge("secondary", {"q0": 1})
    dj = DualJudge(WrongIdJudge(), s)
    with pytest.raises(RuntimeError, match="wrong prompt_id"):
        dj.evaluate([JudgeQuery(prompt_id="q0", gold="g", candidate="c")])


def test_kappa_floor_validation():
    p = ScriptedJudge("primary", {})
    s = ScriptedJudge("secondary", {})
    with pytest.raises(ValueError, match="kappa_floor"):
        DualJudge(p, s, kappa_floor=1.5)


def test_wilson_ci_populated():
    p = ScriptedJudge("primary", {f"q{i}": (1 if i < 7 else 0) for i in range(10)})
    s = ScriptedJudge("secondary", {f"q{i}": (1 if i < 7 else 0) for i in range(10)})
    dj = DualJudge(p, s, kappa_floor=0.6)
    result = dj.evaluate(_queries([f"q{i}" for i in range(10)]))
    low, high = result.primary_pass_rate_ci
    assert 0.0 < low < 0.7 < high < 1.0
