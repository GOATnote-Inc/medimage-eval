"""Hermetic smoke tests — no network, no judge APIs."""

from __future__ import annotations

import math

import pytest

import medimage_eval
from medimage_eval.reporting import cohens_kappa, wilson_ci


def test_version_string():
    assert isinstance(medimage_eval.__version__, str)
    assert medimage_eval.__version__.count(".") >= 2


def test_kappa_perfect_agreement():
    assert cohens_kappa([1, 0, 1, 1, 0], [1, 0, 1, 1, 0]) == pytest.approx(1.0)


def test_kappa_no_correlation_above_chance_is_zero():
    # Worked example from Fleiss (1971): when observed equals expected, κ == 0.
    rater_a = [0] * 5 + [1] * 5
    rater_b = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    assert cohens_kappa(rater_a, rater_b) == pytest.approx(0.0, abs=1e-9)


def test_kappa_canonical_cohen_1960_example():
    # Cohen (1960) Table 1: 2-category, n=200, observed 0.70, expected 0.50 → κ=0.40.
    rater_a = [1] * 100 + [0] * 100
    rater_b = [1] * 75 + [0] * 25 + [1] * 35 + [0] * 65
    kappa = cohens_kappa(rater_a, rater_b)
    assert kappa == pytest.approx(0.40, abs=0.005)


def test_kappa_rejects_empty_input():
    with pytest.raises(ValueError):
        cohens_kappa([], [])


def test_kappa_rejects_mismatched_length():
    with pytest.raises(ValueError):
        cohens_kappa([1, 0], [1, 0, 0])


def test_wilson_ci_midrange():
    low, high = wilson_ci(50, 100)
    assert math.isclose(low, 0.4038, abs_tol=0.005)
    assert math.isclose(high, 0.5962, abs_tol=0.005)


def test_wilson_ci_extreme_one_success():
    low, high = wilson_ci(1, 10)
    # The Wilson interval does not collapse at small successes the way normal-approx does.
    assert low > 0.0
    assert high < 0.5


def test_wilson_ci_no_successes():
    low, high = wilson_ci(0, 10)
    assert low == 0.0
    assert 0.0 < high < 0.35


def test_wilson_ci_rejects_zero_trials():
    with pytest.raises(ValueError):
        wilson_ci(0, 0)


def test_wilson_ci_rejects_more_successes_than_trials():
    with pytest.raises(ValueError):
        wilson_ci(11, 10)
