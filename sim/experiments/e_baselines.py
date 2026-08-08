#!/usr/bin/env python3
"""Matched-budget baseline comparison + route-set phase structure (review R8).

Reviewer ask: compare, under the SAME copy budget K_max and the SAME
energy process (battery B, harvest eta, per-copy cost e=1):

  A. earliest-arrival single-copy CGR (oracle latency; one route's survival)
     -- in our single-energy-bottleneck abstraction, E-CGR's battery
        validation coincides with the energy gate, so the gated k=1
        earliest-arrival baseline IS the E-CGR-style baseline;
  B. RUCoP-style delivery-max replication (energy-blind: k = K_max always);
  C. the proposed freshness-aware policy (two-candidate k*(eta));

and, separately, the effect of the ROUTE-SET phase structure at fixed k:
  locked / independent / anti-phased contact phases.

Model (tier-1, model-exact): per contact period the source fires all-or-
nothing (battery >= k), each of the K_max plan routes is UP independently
w.p. q at delivery time (Tier-2's relay faults give q = 2/3), and a copy
committed to route i realizes residual R_i determined by the route's
contact phase. PAoI accounting is identical to montecarlo.system.

The q = 1 column doubles as a numerical check of the oracle-tie remark
(rem:uncertainty): with no route-outcome uncertainty, earliest-arrival
single-copy CGR ties replication exactly.

Run:  python3 experiments/e_baselines.py
Outputs: results/baselines_paoi.csv, results/routeset_phase.csv
"""
from __future__ import annotations

import csv
import math
import os
import random
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo.battery import poisson          # noqa: E402
from montecarlo.residual import residual        # noqa: E402
from montecarlo.stats import summarize          # noqa: E402
from experiments.e_policy import k_policy       # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

# canonical normalized scenario (delta = W/P as in the R3 experiments)
P, W, T_S = 1.0, 0.15, 0.01
B, K_MAX = 12, 3
Q_FAULT = 2.0 / 3.0            # relay up-probability (Tier-2: down 1/3 of time)
N_PERIODS, WARMUP, SEEDS = 60_000, 2_000, list(range(1, 11))


def _phases(mode: str, k: int, rng: random.Random) -> list:
    """Contact-phase offsets of the k chosen routes for one period."""
    if mode == "locked":                       # all routes share one phase
        u = rng.uniform(0.0, P)
        return [u] * k
    if mode == "anti":                         # evenly staggered plan
        u = rng.uniform(0.0, P)
        return [(u + i * P / k) % P for i in range(k)]
    return [rng.uniform(0.0, P) for _ in range(k)]   # independent


@dataclass
class Run:
    mean_paoi: float
    p_fire: float
    p_del: float                # deliveries per counted period


def simulate(mode: str, k: int, eta: float, q: float, phase_mode: str,
             seed: int, k_max: int = K_MAX) -> Run:
    """mode: 'ea1' = earliest-arrival single-copy over the k_max-route plan
    (oracle latency, single-route survival); 'rep' = commit one copy to each
    of k distinct routes (min over surviving copies)."""
    rng = random.Random(seed)
    b = 0
    last_n = None
    fires = counted = 0
    peak_sum, peak_cnt, deliveries = 0.0, 0, 0
    for n in range(N_PERIODS):
        fired = b >= k
        if fired:
            b -= k
        b = min(B, b + poisson(rng, eta))
        if n < WARMUP:
            if fired and any(rng.random() < q for _ in range(k)):
                last_n = n
            continue
        counted += 1
        if not fired:
            continue
        fires += 1
        # the plan: k_max candidate routes with phase structure phase_mode;
        # CGR route selection = the k earliest-arriving (smallest residual)
        # routes of the plan; each committed copy survives w.p. q.
        phs = _phases(phase_mode, k_max, rng)
        rs = sorted(residual(u, P, W) for u in phs)[:k]
        rs_up = [r for r in rs if rng.random() < q]
        if rs_up:
            deliveries += 1
            rmin = min(rs_up)
            if last_n is not None:
                peak_sum += (n - last_n) * P + rmin + T_S
                peak_cnt += 1
            last_n = n
    return Run(peak_sum / peak_cnt if peak_cnt else float("nan"),
               fires / counted if counted else float("nan"),
               deliveries / counted if counted else float("nan"))


def expA_matched_budgets():
    """Baselines under the same battery/harvest and copy budget, with faults."""
    delta = W / P
    rows = []
    print("\n== A. matched-budget baselines (K_max=%d, q=%.3f, faults on) ==" % (K_MAX, Q_FAULT))
    print(f"{'eta':>5} | {'CGR-EA/E-CGR (k=1)':>20} | {'RUCoP-style (k=K)':>18} | {'k* policy':>16} | k*")
    for eta in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
        ks = k_policy(eta, delta, P, K_MAX)
        cells = {}
        for name, k in (("ea", 1), ("rucop", K_MAX), ("kstar", ks)):
            est = summarize([simulate("rep", k, eta, Q_FAULT, "independent", s).mean_paoi
                             for s in SEEDS])
            cells[name] = est
        print(f"{eta:>5.1f} | {cells['ea'].mean:>9.3f} ±{cells['ea'].ci95:>5.3f}     | "
              f"{cells['rucop'].mean:>8.3f} ±{cells['rucop'].ci95:>5.3f} | "
              f"{cells['kstar'].mean:>7.3f} ±{cells['kstar'].ci95:>5.3f} | {ks}")
        rows.append([eta, ks,
                     cells["ea"].mean, cells["ea"].ci95,
                     cells["rucop"].mean, cells["rucop"].ci95,
                     cells["kstar"].mean, cells["kstar"].ci95])
    with open(os.path.join(RESULTS, "baselines_paoi.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["eta", "k_star", "ea_mean", "ea_ci", "rucop_mean", "rucop_ci",
                    "kstar_mean", "kstar_ci"])
        w.writerows(rows)


def expB_routeset_phase():
    """Route-set phase structure at fixed k=2 over a 2-route plan, with and
    without faults. q=1 doubles as the oracle-tie check."""
    eta = 3.0
    rows = []
    print("\n== B. route-set phase structure (k=2, K_max=2, eta=%.1f) ==" % eta)
    print(f"{'q':>5} | {'set':>12} | {'k=2 PAoI':>16} | {'CGR-EA (k=1) PAoI':>18}")
    for q in (1.0, Q_FAULT):
        for pm in ("locked", "independent", "anti"):
            # EA rides the SAME plan structure (oracle-tie check needs this)
            ea = summarize([simulate("rep", 1, eta, q, pm, s, k_max=2).mean_paoi
                            for s in SEEDS])
            est = summarize([simulate("rep", 2, eta, q, pm, s, k_max=2).mean_paoi
                             for s in SEEDS])
            print(f"{q:>5.3f} | {pm:>12} | {est.mean:>8.4f} ±{est.ci95:>6.4f} | "
                  f"{ea.mean:>9.4f} ±{ea.ci95:>6.4f}")
            rows.append([q, pm, est.mean, est.ci95, ea.mean, ea.ci95])
    with open(os.path.join(RESULTS, "routeset_phase.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["q", "phase_set", "k2_mean", "k2_ci", "ea1_mean", "ea1_ci"])
        w.writerows(rows)


def simulate_adaptive(rule, eta: float, q: float, phase_mode: str,
                      seed: int, k_max: int = K_MAX) -> Run:
    """Like simulate('rep', ...) but the degree is chosen PER EPOCH by
    rule(b) -> k_t (0 = skip). Battery-state-adaptive baselines (review M11)."""
    rng = random.Random(seed)
    b = 0
    last_n = None
    fires = counted = 0
    peak_sum, peak_cnt, deliveries = 0.0, 0, 0
    for n in range(N_PERIODS):
        k_t = rule(b)
        fired = k_t > 0 and b >= k_t
        if fired:
            b -= k_t
        b = min(B, b + poisson(rng, eta))
        if n < WARMUP:
            if fired and any(rng.random() < q for _ in range(min(k_t, k_max))):
                last_n = n
            continue
        counted += 1
        if not fired:
            continue
        fires += 1
        kc = min(k_t, k_max)
        phs = _phases(phase_mode, k_max, rng)
        rs = sorted(residual(u, P, W) for u in phs)[:kc]
        rs_up = [r for r in rs if rng.random() < q]
        if rs_up:
            deliveries += 1
            rmin = min(rs_up)
            if last_n is not None:
                peak_sum += (n - last_n) * P + rmin + T_S
                peak_cnt += 1
            last_n = n
    return Run(peak_sum / peak_cnt if peak_cnt else float("nan"),
               fires / counted if counted else float("nan"),
               deliveries / counted if counted else float("nan"))


def expC_adaptive_baselines():
    """Battery-state-adaptive rules vs the mean-based two-candidate set-point,
    same faults/energy: greedy (fire whatever the battery holds, capped K_max)
    and threshold (all-in K_max iff affordable, else minimal single copy)."""
    delta = W / P
    rows = []
    print("\n== C. adaptive baselines (faults on, q=%.3f) ==" % Q_FAULT)
    print(f"{'eta':>5} | {'k* set-point':>14} | {'battery-greedy':>14} | {'battery-thresh':>14} | best")
    for eta in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
        ks = k_policy(eta, delta, P, K_MAX)
        ours = summarize([simulate("rep", ks, eta, Q_FAULT, "independent", s).mean_paoi
                          for s in SEEDS])
        greedy = summarize([simulate_adaptive(
            lambda bb: min(K_MAX, int(bb)) if bb >= 1 else 0,
            eta, Q_FAULT, "independent", s).mean_paoi for s in SEEDS])
        thresh = summarize([simulate_adaptive(
            lambda bb: K_MAX if bb >= K_MAX else (1 if bb >= 1 else 0),
            eta, Q_FAULT, "independent", s).mean_paoi for s in SEEDS])
        vals = {"kstar": ours.mean, "greedy": greedy.mean, "thresh": thresh.mean}
        best = min(vals, key=vals.get)
        print(f"{eta:>5.1f} | {ours.mean:>7.3f} ±{ours.ci95:>5.3f} | "
              f"{greedy.mean:>7.3f} ±{greedy.ci95:>5.3f} | "
              f"{thresh.mean:>7.3f} ±{thresh.ci95:>5.3f} | {best}")
        rows.append([eta, ks, ours.mean, ours.ci95, greedy.mean, greedy.ci95,
                     thresh.mean, thresh.ci95, best])
    with open(os.path.join(RESULTS, "baselines_adaptive.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["eta", "k_star", "kstar_mean", "kstar_ci", "greedy_mean",
                    "greedy_ci", "thresh_mean", "thresh_ci", "best"])
        w.writerows(rows)


if __name__ == "__main__":
    expA_matched_budgets()
    expB_routeset_phase()
    expC_adaptive_baselines()
    print("\nwrote results/baselines_paoi.csv, results/routeset_phase.csv, "
          "results/baselines_adaptive.csv")
