"""Inter-rater agreement and proportion-confidence statistics.

Two primitives the substrate leans on everywhere:

* `cohens_kappa` — chance-corrected agreement between two raters. Floor-checked
  against published examples in Cohen (1960) and Fleiss (1971).
* `wilson_ci` — Wilson score 95% CI for a binomial proportion. Better than
  normal-approx for the small-n stratified slices the shift gauntlet produces.

Both are textbook implementations; tests pin them to canonical worked examples.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def cohens_kappa(rater_a: Sequence[int], rater_b: Sequence[int]) -> float:
    """Compute Cohen's kappa for two raters over a common categorical set.

    Args:
        rater_a: integer category labels from rater A.
        rater_b: integer category labels from rater B, aligned with `rater_a`.

    Returns:
        Cohen's kappa as a float in [-1.0, 1.0].

    Raises:
        ValueError: if inputs are empty or of unequal length.
    """
    if len(rater_a) != len(rater_b):
        raise ValueError("rater_a and rater_b must be the same length")
    n = len(rater_a)
    if n == 0:
        raise ValueError("rater_a and rater_b must not be empty")

    categories = sorted(set(rater_a) | set(rater_b))
    cat_index = {c: i for i, c in enumerate(categories)}
    k = len(categories)

    matrix = [[0] * k for _ in range(k)]
    for a, b in zip(rater_a, rater_b, strict=True):
        matrix[cat_index[a]][cat_index[b]] += 1

    observed = sum(matrix[i][i] for i in range(k)) / n
    row_totals = [sum(matrix[i]) for i in range(k)]
    col_totals = [sum(matrix[i][j] for i in range(k)) for j in range(k)]
    expected = sum((row_totals[i] * col_totals[i]) for i in range(k)) / (n * n)

    if math.isclose(expected, 1.0):
        return 1.0 if math.isclose(observed, 1.0) else 0.0

    return (observed - expected) / (1.0 - expected)


def wilson_ci(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score confidence interval for a binomial proportion.

    Args:
        successes: number of successes.
        trials: number of trials. Must be positive.
        confidence: confidence level in (0, 1). Default 0.95.

    Returns:
        (low, high) bounds of the Wilson interval, each in [0.0, 1.0].

    Raises:
        ValueError: on invalid inputs.
    """
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must be in [0, trials]")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")

    z = _z_for_confidence(confidence)
    p = successes / trials
    denom = 1.0 + (z * z) / trials
    centre = (p + (z * z) / (2.0 * trials)) / denom
    half = (z * math.sqrt(p * (1.0 - p) / trials + (z * z) / (4.0 * trials * trials))) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _z_for_confidence(confidence: float) -> float:
    """Inverse-normal CDF for a two-sided confidence level.

    We don't pull in scipy for this single call — the inverse-normal series
    converges fast and is accurate to ~1e-6 in the range we use.
    """
    alpha = 1.0 - confidence
    p = 1.0 - alpha / 2.0
    return _ndtri(p)


def _ndtri(p: float) -> float:
    """Beasley-Springer-Moro approximation to the inverse normal CDF."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")

    a = [
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    ]
    b = [
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    ]
    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    ]

    p_low = 0.02425
    p_high = 1.0 - p_low

    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        return num / den
    if p > p_high:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        return -num / den
    q = p - 0.5
    r = q * q
    num = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    den = (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    return num / den
