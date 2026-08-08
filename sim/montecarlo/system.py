"""Integrated energy + replication + AoI system (Result 3, sec 6.3-6.4).

Couples the battery throttle (all-or-nothing firing) with order-statistic
replication over independent LEO contacts, and measures the realized mean
PAoI as a function of the replication degree k.

Per contact period n:
  - fire k copies iff battery b >= k  (consume k);
  - on a firing, the delivered freshness is the min residual over
    min(k, K_max) independent satellites (copies beyond K_max ride
    correlated contacts: no extra gain, but still cost energy);
  - harvest A ~ Poisson(eta), cap at B.

Mean PAoI^per (per-update peak under paced generation; NOT the
generate-at-will outage peak OPAoI of Result 1) =
P/p_e + E[R_min, min(k,K_max)] + T_s. The starvation part
P/p_e and the analytic A(k) of sec 6.3 differ only by the constant P, so
the argmin over k is identical -- this is the end-to-end check of
  k* = min(K_max, floor(eta)),  monotonicity in eta, and saturation.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .battery import poisson
from .residual import residual


@dataclass
class R3Run:
    mean_paoi: float
    p_e: float
    mean_Rmin: float
    n_deliveries: int


def simulate_r3_paoi(P: float, W: float, T_s: float, k: int, eta: float,
                     B: int, K_max: int, n_periods: int, seed: int,
                     warmup_periods: int = 1000, alpha: float = 1.0) -> R3Run:
    """alpha = contact-prediction reliability: each committed copy's
    predicted contact materializes (delivers) w.p. alpha; energy is spent
    on the commit regardless, so copies sent to missed contacts are wasted.
    alpha=1 recovers the perfect-prediction model."""
    rng = random.Random(seed)
    kc = min(k, K_max)            # independent contacts actually exploited
    b = 0
    last_n = None                 # period index of previous delivery
    fires = 0
    counted = 0
    peak_sum = 0.0
    peak_cnt = 0
    rmin_sum = 0.0

    for n in range(n_periods):
        fired = b >= k
        if fired:
            b -= k
        A = poisson(rng, eta)
        b = min(B, b + A)

        if n < warmup_periods:
            if fired:
                last_n = n
            continue

        counted += 1
        if fired:
            fires += 1
            # each copy's predicted contact materializes w.p. alpha
            materialized = [residual(rng.uniform(0.0, P), P, W)
                            for _ in range(kc) if alpha >= 1.0 or rng.random() < alpha]
            if materialized:
                rmin = min(materialized)
                rmin_sum += rmin
                if last_n is not None:
                    gap = n - last_n          # periods since previous delivery
                    peak_sum += gap * P + rmin + T_s
                    peak_cnt += 1
                last_n = n
            # else: energy spent but no copy materialized -> no delivery

    p_e = fires / counted if counted else float("nan")
    mean_paoi = peak_sum / peak_cnt if peak_cnt else float("nan")
    mean_rmin = rmin_sum / fires if fires else float("nan")
    return R3Run(mean_paoi, p_e, mean_rmin, peak_cnt)


def k_star_cf(eta: float, K_max: int) -> int:
    """Closed-form optimal degree: min(K_max, floor(eta)), >= 1."""
    return max(1, min(K_max, int(math.floor(eta))))


def r3_peaks(P: float, W: float, T_s: float, k: int, eta: float,
             B: int, K_max: int, n_periods: int, seed: int,
             warmup_periods: int = 1000) -> list:
    """Return the list of per-cycle PAoI peaks (for tail / CCDF analysis)."""
    rng = random.Random(seed)
    kc = min(k, K_max)
    b = 0
    last_n = None
    peaks = []
    for n in range(n_periods):
        fired = b >= k
        if fired:
            b -= k
        b = min(B, b + poisson(rng, eta))
        if n < warmup_periods:
            if fired:
                last_n = n
            continue
        if fired:
            rmin = min(residual(rng.uniform(0.0, P), P, W) for _ in range(kc))
            if last_n is not None:
                peaks.append((n - last_n) * P + rmin + T_s)
            last_n = n
    return peaks
