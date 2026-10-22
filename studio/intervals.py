"""Exact and score intervals on small counts: the one helper every bench reads.

    cp_upper(0, 60)       -> 0.0487   one-sided 95 % Clopper-Pearson upper bound
    cp_lower(26, 30)      -> 0.7203   one-sided 95 % lower bound
    clopper_pearson(k, n) -> (low, high), two-sided 95 %
    wilson(k, n)          -> (low, high), the Wilson score interval

At casebook counts (tens of owner rows) the normal approximation lies, so a
promotion bar is read off the exact binomial (fleet H ruling A3).  Nothing
counted is no knowledge: n = 0 gives (0, 1), never (0, 0).  Pure Python, the
binomial tail summed in log space and inverted by bisection.
"""
from __future__ import annotations

import math

Z95 = 1.959964
_STEPS = 60


def _check(k: int, n: int) -> None:
    if n < 0 or k < 0 or k > n:
        raise ValueError(f"{k} successes in {n} trials is not a count")


def binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p), summed in log space so large n never overflows."""
    if p <= 0.0 or k >= n:
        return 1.0
    if p >= 1.0:
        return 0.0
    lp, lq, ln = math.log(p), math.log1p(-p), math.lgamma(n + 1)
    return min(1.0, sum(math.exp(ln - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq)
                        for i in range(k + 1)))


def _bisect(falls, low: float = 0.0, high: float = 1.0) -> float:
    """The p in [low, high] where the monotone test `falls(p)` turns true."""
    for _ in range(_STEPS):
        mid = (low + high) / 2
        low, high = (low, mid) if falls(mid) else (mid, high)
    return (low + high) / 2


def cp_upper(k: int, n: int, conf: float = 0.95) -> float:
    """The one-sided exact upper bound: the largest p with P(X <= k | p) >= 1 - conf."""
    _check(k, n)
    if k == n:
        return 1.0
    return round(_bisect(lambda p: binom_cdf(k, n, p) < 1 - conf), 4)


def cp_lower(k: int, n: int, conf: float = 0.95) -> float:
    """The one-sided exact lower bound: the smallest p with P(X >= k | p) >= 1 - conf."""
    _check(k, n)
    if k == 0:
        return 0.0
    return round(_bisect(lambda p: 1 - binom_cdf(k - 1, n, p) >= 1 - conf), 4)


def clopper_pearson(k: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """The two-sided exact interval: half the error on each side; (0, 1) on nothing counted."""
    side = 1 - (1 - conf) / 2
    return cp_lower(k, n, side), cp_upper(k, n, side)


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """The Wilson score interval of k successes in n; (0, 1) when there is nothing to count."""
    _check(k, n)
    if n == 0:
        return 0.0, 1.0
    p, z2 = k / n, z * z
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)
