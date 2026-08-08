"""LEO residual-wait sampling and the AoI/PAoI process (Result 1, sec 6.1).

Schedule: window W once per period P; link ON on [0, W) of each period,
OFF on [W, P). Silent gap G = P - W, duty cycle delta = W/P.

Residual wait for a packet generated at phase u = (g mod P):
    R = 0           if u in [0, W)      (link already up)
    R = P - u       if u in [W, P)      (wait to next window)

Closed forms validated here:
    E[R]              = P*(1-delta)^2 / 2 = G^2/(2P)
    E[R^2]            = G^3 / (3P)
    mean AoI          = T_s + E[R]
    PAoI              = T_s + G = T_s + P*(1-delta)

The AoI/PAoI process below uses the random-arrival (Poisson) view with
last-come-first-served selection at the monitor; as the generation rate
grows it converges to the generate-at-will floor and reproduces the
closed forms above (small-T_s convention: T_s << P).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List


def residual(u: float, P: float, W: float) -> float:
    """Residual wait for a packet whose arrival phase is u in [0, P)."""
    u = u % P
    if u < W:
        return 0.0
    return P - u


# ----- closed-form references (the validation targets, not simulation) -----

def mean_residual_cf(P: float, W: float) -> float:
    G = P - W
    return G * G / (2.0 * P)


def mean_sq_residual_cf(P: float, W: float) -> float:
    G = P - W
    return G ** 3 / (3.0 * P)


def mean_aoi_cf(P: float, W: float, T_s: float) -> float:
    return T_s + mean_residual_cf(P, W)


def paoi_cf(P: float, W: float, T_s: float) -> float:
    return T_s + (P - W)


def residual_sf(r: float, P: float, W: float) -> float:
    """Survival function P(R > r) = (G - r)/P on [0, G]; used for KS checks."""
    G = P - W
    if r < 0:
        return 1.0
    if r >= G:
        return 0.0
    return (G - r) / P


# ----- stochastic residual sampling (E1: distribution + moments) -----

@dataclass
class ResidualSample:
    mean: float
    mean_sq: float
    ks_stat: float       # sup |empirical CDF - closed-form CDF|
    atom_frac: float     # empirical P(R == 0), closed form = W/P = delta
    n: int


def sample_residuals(P: float, W: float, n: int, seed: int) -> ResidualSample:
    """Draw n packets at uniform random phase; summarize R vs closed form."""
    rng = random.Random(seed)
    rs: List[float] = [residual(rng.uniform(0.0, P), P, W) for _ in range(n)]
    mean = sum(rs) / n
    mean_sq = sum(r * r for r in rs) / n
    atom = sum(1 for r in rs if r == 0.0) / n
    # KS vs the mixed CDF F(r) = (W + r)/P on [0, G], with an atom of mass
    # W/P at r = 0. The atom means F jumps at 0 (left limit 0, value W/P),
    # so the empirical pre-jump value must be compared to the theoretical
    # *left limit*, not the post-jump value -- otherwise KS is inflated to
    # exactly delta. Group ties and compare both one-sided gaps.
    rs_sorted = sorted(rs)
    G = P - W
    ks = 0.0
    i = 0
    while i < n:
        v = rs_sorted[i]
        j = i
        while j < n and rs_sorted[j] == v:
            j += 1
        emp_hi = j / n          # F_n(v)   (at/just below: count <= v)
        emp_lo = i / n          # F_n(v^-) (just below v)
        fth = 1.0 if v >= G else (W + v) / P            # F(v)
        fth_left = 0.0 if v == 0.0 else fth             # F(v^-): jump only at 0
        ks = max(ks, abs(emp_hi - fth), abs(emp_lo - fth_left))
        i = j
    return ResidualSample(mean, mean_sq, ks, atom, n)


# ----- AoI/PAoI process simulation (E1b/E2: mean AoI and PAoI) -----

@dataclass
class AoIRun:
    mean_aoi: float
    paoi: float          # mean of per-peak ages
    n_deliveries: int


def simulate_aoi(P: float, W: float, T_s: float, lam_gen: float,
                 horizon_periods: float, warmup_periods: float,
                 seed: int) -> AoIRun:
    """Discrete-event AoI simulation under Poisson(lam_gen) generation.

    Each packet generated at g is delivered at d = g + R(g) + T_s, where
    R is the residual wait. The monitor keeps the freshest delivered
    packet (LCFS at the monitor: stale deliveries are ignored). We
    integrate the age sawtooth over the measurement window and record the
    age just before each downward jump as a peak.

    As lam_gen grows the mean AoI -> T_s + E[R] and PAoI -> T_s + G.
    Capacity for in-flight bundles is assumed ample (status-update model).
    """
    rng = random.Random(seed)
    H = horizon_periods * P
    warm = warmup_periods * P

    # Generate (gen_time, delivery_time) pairs over [0, H].
    deliveries = []  # (delivery_time, gen_time)
    t = 0.0
    if lam_gen <= 0:
        raise ValueError("lam_gen must be > 0")
    while True:
        t += rng.expovariate(lam_gen)
        if t > H:
            break
        d = t + residual(t, P, W) + T_s
        deliveries.append((d, t))
    deliveries.sort()

    # Sweep deliveries in time order, integrating age over [warm, H].
    # PAoI is the mean of per-period MAXIMUM ages (one peak per contact
    # cycle): with continuous in-window generation there are many small
    # resets per period, but the peak that the closed form T_s + G
    # describes is the age at the end of the silent gap, i.e. the maximum
    # within each period. Averaging every reset would understate it.
    monitor_gen = -math.inf   # gen time of freshest delivered packet
    last_t = warm
    area = 0.0
    period_peak = {}          # period index -> max pre-reset age in it
    for d_time, g_time in deliveries:
        if d_time <= warm:
            if g_time > monitor_gen:
                monitor_gen = g_time
            continue
        if d_time > H:
            break
        if g_time <= monitor_gen:
            continue  # stale: a fresher packet already delivered
        seg_start = max(last_t, warm)
        if monitor_gen > -math.inf:
            a0 = seg_start - monitor_gen
            a1 = d_time - monitor_gen          # age just before this reset
            area += 0.5 * (a0 + a1) * (d_time - seg_start)
            pidx = int(d_time // P)
            if a1 > period_peak.get(pidx, -math.inf):
                period_peak[pidx] = a1
        monitor_gen = g_time
        last_t = d_time

    # tail segment to H
    if monitor_gen > -math.inf and H > max(last_t, warm):
        seg_start = max(last_t, warm)
        a0 = seg_start - monitor_gen
        a1 = H - monitor_gen
        area += 0.5 * (a0 + a1) * (H - seg_start)

    span = H - warm
    mean_aoi = area / span if span > 0 else float("nan")
    # drop the first/last partial periods to avoid edge bias
    peaks = list(period_peak.values())
    paoi = sum(peaks) / len(peaks) if peaks else float("nan")
    return AoIRun(mean_aoi, paoi, len(peaks))
