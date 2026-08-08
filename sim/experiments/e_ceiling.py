#!/usr/bin/env python3
"""E14 -- ceiling-region validation of the two-candidate rule (P1-8).

Prior energy experiments (E7/E8) only sampled integer or half-integer eta,
so the skip-aware CEILING branch of the optimum -- k* = ceil(eta) winning
over floor(eta) inside a non-integer interval -- was never exercised. This
experiment sweeps eta finely across a single integer interval [m, m+1] and
checks that the SIMULATED PAoI-optimal degree flips from floor(eta) to
ceil(eta) exactly at the analytic crossover of eq:ceiltest, i.e. where
    P*(ceil/eta - 1)  ==  g_floor - g_ceil ,   g_k = P(1-delta)^{k+1}/(k+1).

With delta=0.1 and interval [3,4] the crossover sits near eta ~ 3.8, so
k*=3 for eta<~3.8 and k*=4 (=ceil) above -- a clean ceiling win.

Run (on the VM):
    python3 experiments/e_ceiling.py            # full
    python3 experiments/e_ceiling.py --quick
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import system as S                 # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def A_analytic(k, eta, delta, P):
    pe = min(1.0, eta / k)
    starv = P * (1 - pe) / pe if pe > 0 else float("inf")
    gain = P * (1 - delta) ** (k + 1) / (k + 1)
    return starv + gain


def analytic_crossover(m, delta, P):
    """eta in (m, m+1) where A(m) == A(m+1); None if ceil never wins here."""
    lo, hi = m, m + 1.0
    f = lambda e: A_analytic(m + 1, e, delta, P) - A_analytic(m, e, delta, P)
    # f(lo^+) > 0 (floor wins near m), f(hi) < 0 (ceil wins near m+1) expected
    if f(lo + 1e-6) < 0:            # ceil already wins across the interval
        return lo
    if f(hi) > 0:                   # floor wins across the interval
        return None
    for _ in range(60):             # bisection on the sign change
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--W", type=float, default=0.10)
    ap.add_argument("--Ts", type=float, default=0.005)
    ap.add_argument("--B", type=int, default=64)
    ap.add_argument("--Kmax", type=int, default=5)
    ap.add_argument("--m", type=int, default=3, help="integer interval [m, m+1]")
    ap.add_argument("--periods", type=int, default=200000)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.periods, args.seeds = 20000, 6
    os.makedirs(RESULTS, exist_ok=True)
    P, W, Ts, B, Kmax, m = args.P, args.W, args.Ts, args.B, args.Kmax, args.m
    delta = W / P

    xover = analytic_crossover(m, delta, P)
    print(f"delta={delta}, interval [{m},{m+1}], K_max={Kmax}")
    if xover is None:
        print(f"analytic: floor(eta)={m} wins across the whole interval "
              f"(ceiling never wins here)")
    else:
        print(f"analytic crossover eta* = {xover:.4f}  "
              f"(k*={m} below, k*={m+1} above)")

    etas = [m + 0.1 * i for i in range(1, 10)]     # m+0.1 .. m+0.9
    rows = []
    ok = 0
    print("\neta    PAoI[k=m..m+2]                 k_sim  k_analytic  match")
    for eta in etas:
        paoi = {}
        for k in (m, m + 1, m + 2):
            if k < 1 or k > Kmax:
                continue
            vals = [S.simulate_r3_paoi(P, W, Ts, k, eta, B, Kmax, args.periods,
                                       seed=14000 + s, warmup_periods=args.warmup).mean_paoi
                    for s in range(args.seeds)]
            paoi[k] = sum(vals) / len(vals)
        k_sim = min(paoi, key=paoi.get)
        k_an = m if (xover is None or eta < xover) else m + 1
        good = (k_sim == k_an)
        ok += good
        curve = " ".join(f"k{k}:{v:.4f}" for k, v in sorted(paoi.items()))
        print(f"{eta:.1f}   {curve}   {k_sim}      {k_an}       {'OK' if good else 'x'}")
        rows.append(dict(eta=round(eta, 2), k_sim=k_sim, k_analytic=k_an,
                         crossover=round(xover, 4) if xover else "",
                         **{f"paoi_k{k}": v for k, v in paoi.items()}))
    with open(os.path.join(RESULTS, "ceiling_sweep.csv"), "w", newline="") as f:
        fields = sorted({key for r in rows for key in r})
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"\nsimulated optimum matches analytic branch in {ok}/{len(etas)} points")
    print(f"-> wrote {os.path.join(RESULTS, 'ceiling_sweep.csv')}")
    print("PASS" if ok >= len(etas) - 1 else "CHECK")


if __name__ == "__main__":
    main()
