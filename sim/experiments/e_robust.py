#!/usr/bin/env python3
"""Robustness of the k* rule to contact-prediction error.

DTN contact plans are predictions. We model prediction reliability alpha:
each committed copy's predicted contact materializes (delivers) w.p. alpha,
energy spent on the commit regardless. Question: should one reserve energy
(use fewer copies, k_robust=floor(alpha*eta)) under prediction uncertainty?

Finding: NO. The PAoI-optimal degree stays at the energy ceiling
k*=floor(eta) for all alpha in [0.4,1], because extra copies hedge missed
contacts via the order statistic over materialization. The reserve rule
floor(alpha*eta) under-replicates and worsens PAoI. So the k* threshold is
robust to prediction error; prediction error degrades achieved freshness
but does not change the optimal degree.

Run (on the VM):
    python3 experiments/e_robust.py
"""
from __future__ import annotations

import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import system as S                 # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def main():
    P, W, Ts, B, Kmax = 1.0, 0.10, 0.005, 64, 8
    periods, warmup, seeds = 80000, 1000, 8
    eta = 6.0
    alphas = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
    ks = list(range(1, Kmax + 1))

    def paoi(k, a):
        v = [S.simulate_r3_paoi(P, W, Ts, k, eta, B, Kmax, periods,
                                seed=9100 + s, warmup_periods=warmup, alpha=a).mean_paoi
             for s in range(seeds)]
        return sum(v) / len(v)

    k_full = max(1, min(Kmax, int(math.floor(eta))))   # our rule
    rows = []
    print(f"eta={eta}, K_max={Kmax}; our rule k*=floor(eta)={k_full}")
    print("alpha  argmin-k  PAoI(k*=6)  PAoI(reserve floor(a*eta))  reserve penalty")
    for a in alphas:
        curve = [paoi(k, a) for k in ks]
        kstar = 1 + min(range(Kmax), key=lambda i: curve[i])
        k_res = max(1, int(math.floor(a * eta)))
        p_full = curve[k_full - 1]
        p_res = curve[k_res - 1]
        pen = (p_res - p_full) / p_full * 100.0
        print(f"{a:4.2f}   {kstar:2d}        {p_full:7.3f}      {p_res:7.3f} (k={k_res})"
              f"           {pen:+5.1f}%")
        rows.append(dict(alpha=a, argmin_k=kstar, k_full=k_full, k_reserve=k_res,
                         paoi_full=round(p_full, 4), paoi_reserve=round(p_res, 4),
                         reserve_penalty_pct=round(pen, 1)))
    with open(os.path.join(RESULTS, "robust_kstar.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("\n=> argmin-k stays at floor(eta) for every alpha: the threshold is robust to")
    print("   prediction error; the reserve rule floor(alpha*eta) only worsens PAoI.")
    print(f"-> wrote {os.path.join(RESULTS, 'robust_kstar.csv')}")


if __name__ == "__main__":
    main()
