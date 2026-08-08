"""Replication statistics: mean and confidence interval over seeds.

We report results as the mean over independent seeded replications with a
95% confidence interval. For n >= 30 the normal approximation is used
(z = 1.96); a short Student-t table covers small n.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Sequence

# Student-t 97.5% critical values for small samples (two-sided 95% CI).
_T_975 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    15: 2.131, 20: 2.086, 25: 2.060, 29: 2.045,
}


def _t_crit(df: int) -> float:
    if df >= 30:
        return NormalDist().inv_cdf(0.975)  # ~1.96
    if df in _T_975:
        return _T_975[df]
    # nearest tabulated df below
    keys = sorted(k for k in _T_975 if k <= df) or [1]
    return _T_975[keys[-1]]


@dataclass
class Estimate:
    """Point estimate with a symmetric 95% CI half-width."""
    mean: float
    ci95: float
    n: int

    @property
    def lo(self) -> float:
        return self.mean - self.ci95

    @property
    def hi(self) -> float:
        return self.mean + self.ci95

    def contains(self, x: float) -> bool:
        """Does the 95% CI cover the value x (e.g. a closed-form target)?"""
        return self.lo <= x <= self.hi

    def rel_error(self, target: float) -> float:
        if target == 0:
            return abs(self.mean)
        return abs(self.mean - target) / abs(target)

    def __str__(self) -> str:
        return f"{self.mean:.6g} +/- {self.ci95:.3g} (n={self.n})"


def summarize(samples: Sequence[float]) -> Estimate:
    """Mean and 95% CI half-width over independent replications."""
    n = len(samples)
    if n == 0:
        raise ValueError("no samples")
    mean = sum(samples) / n
    if n == 1:
        return Estimate(mean, float("inf"), 1)
    var = sum((x - mean) ** 2 for x in samples) / (n - 1)
    se = math.sqrt(var / n)
    half = _t_crit(n - 1) * se
    return Estimate(mean, half, n)
