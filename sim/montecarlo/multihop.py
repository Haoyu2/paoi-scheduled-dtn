"""Multi-hop / multi-copy residual machinery (Results 2, sec 6.2).

Covers:
  E3  phase-mixing lemma -- incommensurate periods decouple the
      downstream phase from the upstream increment; commensurate periods
      lock it.
  E4  k=2 order-statistic gain  E[R]-E[R_min] = (1/2) E|R1-R2|, and the
      worked-example ratio E[R_min]/E[R] = (2/3)(1-delta).
  E5  same-bottleneck copies -> gain collapses to 0.
  E6  windows staggered by P/2 -> worst-case residual ~ P/2 - W.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List

from .residual import residual


def residual_min_cf(P: float, W: float, k: int) -> float:
    """Closed form E[R_min,k] = G^{k+1} / ((k+1) P^k), G = P - W."""
    G = P - W
    return G ** (k + 1) / ((k + 1) * P ** k)


def _pearson(xs: List[float], ys: List[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


# ----- E3: phase mixing -------------------------------------------------

@dataclass
class PhaseMixRun:
    ks_uniform: float    # KS of downstream phase Phi_2 to Unif[0, P2)
    corr_R2_D1: float    # Pearson corr between R2 and the upstream increment
    n: int


def two_hop_phase(P1: float, W1: float, T1: float,
                  P2: float, W2: float, n_packets: int, seed: int) -> PhaseMixRun:
    """Packets arrive at segment 1 once per its period at a random in-period
    phase; we track the phase seen at segment 2, Phi_2 = (n*P1 + u + D1) mod P2,
    and its coupling to the upstream increment D1 = R1 + T1.

    Incommensurate P1/P2: {n*P1 mod P2} equidistributes (Weyl) -> Phi_2
    uniform and R2 independent of D1. Commensurate (P1 == P2): the n*P1
    term vanishes mod P2 -> Phi_2 determined by D1 -> locked.
    """
    rng = random.Random(seed)
    phis: List[float] = []
    r2s: List[float] = []
    d1s: List[float] = []
    for n in range(n_packets):
        u = rng.uniform(0.0, P1)
        a1 = n * P1 + u                 # arrival time at segment 1
        D1 = residual(u, P1, W1) + T1   # increment through segment 1
        phi2 = (a1 + D1) % P2
        phis.append(phi2)
        r2s.append(residual(phi2, P2, W2))
        d1s.append(D1)
    # KS of Phi_2 to Unif[0, P2)
    phis_sorted = sorted(phis)
    n = len(phis_sorted)
    ks = 0.0
    for i, v in enumerate(phis_sorted):
        cdf = v / P2
        ks = max(ks, abs((i + 1) / n - cdf), abs(cdf - i / n))
    return PhaseMixRun(ks, _pearson(r2s, d1s), n)


# ----- E4/E5/E6: order-statistic gain ----------------------------------

@dataclass
class GainRun:
    mean_R: float
    mean_Rmin: float
    half_mean_absdiff: float   # (1/2) E|R1 - R2|
    ratio_min_over_R: float    # E[R_min]/E[R]
    max_Rmin: float
    n: int


def two_copy_gain(P: float, W: float, n: int, seed: int,
                  same_bottleneck: bool = False,
                  stagger: float = 0.0) -> GainRun:
    """Two independent-phase copies over LEO; measure the k=2 gain.

    same_bottleneck=True  -> both copies share one satellite (R1 == R2).
    stagger>0             -> second satellite's window offset by `stagger`
                             (use P/2 for E6).
    """
    rng = random.Random(seed)
    Rs, Rmins, absdiffs = [], [], []
    for _ in range(n):
        u1 = rng.uniform(0.0, P)
        r1 = residual(u1, P, W)
        if same_bottleneck:
            r2 = r1
        else:
            # second satellite: independent phase; optional window stagger
            u2 = rng.uniform(0.0, P)
            r2 = residual((u2 - stagger) % P, P, W) if stagger else residual(u2, P, W)
        Rs.append(r1)
        Rmins.append(min(r1, r2))
        absdiffs.append(abs(r1 - r2))
    mR = sum(Rs) / n
    mRmin = sum(Rmins) / n
    half_abs = 0.5 * sum(absdiffs) / n
    return GainRun(mR, mRmin, half_abs, mRmin / mR if mR else float("nan"),
                   max(Rmins), n)


def staggered_max_residual(P: float, W: float, n: int, seed: int) -> float:
    """Worst-case delivered residual for two windows offset by P/2.

    Closed form: the largest gap to the nearer window is P/2 - W, so the
    worst-case (max) min-residual is P/2 - W (vs P - W single-satellite).
    """
    rng = random.Random(seed)
    worst = 0.0
    for _ in range(n):
        u = rng.uniform(0.0, P)
        r1 = residual(u, P, W)
        r2 = residual((u - P / 2.0) % P, P, W)
        worst = max(worst, min(r1, r2))
    return worst
