#!/usr/bin/env python3
"""E11 -- sec 6.4 finite-battery conservative shift.

Work conservation gives p_e <= min(1, eta/k), with the gap = overflow
loss L that grows as the battery capacity B shrinks. A smaller p_e
inflates the starvation term for k > eta, so the PAoI-optimal degree can
only move DOWN: the true k* <= floor(eta), and k*(B) is non-increasing
as B shrinks.

Sweep B at fixed eta; check k*(B) is non-increasing and all <= floor(eta).

Run (on the VM):
    python3 experiments/e11_finiteB.py
    python3 experiments/e11_finiteB.py --quick
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import system as S                  # noqa: E402
from montecarlo.battery import simulate_battery, p_e_fluid   # noqa: E402


def mean_paoi_seeds(P, W, Ts, k, eta, B, Kmax, periods, warmup, seeds):
    vals = [S.simulate_r3_paoi(P, W, Ts, k, eta, B, Kmax, periods,
                               seed=9000 + s, warmup_periods=warmup).mean_paoi
            for s in range(seeds)]
    return sum(vals) / len(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--W", type=float, default=0.10)
    ap.add_argument("--Ts", type=float, default=0.005)
    ap.add_argument("--Kmax", type=int, default=8)
    ap.add_argument("--periods", type=int, default=80000)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.periods, args.warmup, args.seeds = 15000, 500, 4

    RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    os.makedirs(RESULTS, exist_ok=True)
    P, W, Ts, Kmax = args.P, args.W, args.Ts, args.Kmax
    ks = list(range(1, Kmax + 2))

    rows = []
    all_ok = True
    for eta in [4.0, 6.0]:
        floor_eta = int(eta)
        print(f"=== E11 finite-B conservative shift, eta={eta}, floor(eta)={floor_eta} ===")
        Bvals = [64, floor_eta + 2, floor_eta + 1, floor_eta]
        kstars = []
        for B in Bvals:
            ys = [mean_paoi_seeds(P, W, Ts, k, eta, B, Kmax,
                                  args.periods, args.warmup, args.seeds) for k in ks]
            kstar = ks[min(range(len(ys)), key=lambda i: ys[i])]
            kstars.append(kstar)
            # measured throttle at k = floor(eta) to show the p_e degradation
            br = simulate_battery(B, floor_eta, eta, args.periods, seed=9100,
                                  warmup_periods=args.warmup)
            print(f"  B={B:3d}  k*={kstar}  p_e(k={floor_eta})={br.p_e:.4f} "
                  f"(fluid {p_e_fluid(floor_eta, eta):.4f}, overflow L={br.overflow_L:.4f})")
            rows.append(dict(eta=eta, B=B, k_star=kstar, p_e=br.p_e,
                             p_e_fluid=p_e_fluid(floor_eta, eta), overflow_L=br.overflow_L))
        # non-increasing as B shrinks (Bvals already large->small) and all <= floor(eta)
        nonincr = all(kstars[i] >= kstars[i + 1] for i in range(len(kstars) - 1))
        bounded = all(ks_ <= floor_eta for ks_ in kstars)
        ok = nonincr and bounded
        all_ok = all_ok and ok
        print(f"  k*(B) = {kstars} (B={Bvals})  non-increasing={nonincr}  "
              f"all<=floor(eta)={bounded}  {'OK' if ok else 'FAIL'}")

    with open(os.path.join(RESULTS, "e11_finite_battery.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  -> wrote {os.path.join(RESULTS, 'e11_finite_battery.csv')}")
    print(f"\nE11 {'PASS' if all_ok else 'FAIL'}")


if __name__ == "__main__":
    main()
