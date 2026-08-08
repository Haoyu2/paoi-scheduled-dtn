#!/usr/bin/env python3
"""PAoI tail / deadline-violation evaluation (mission-critical metric).

For mission-critical traffic the relevant quantity is not mean PAoI but
the tail: P(PAoI > deadline). Replication shrinks the delivered residual
via the order statistic, so it should pull the PAoI tail in. At a fixed
(energy-abundant) eta we collect per-cycle PAoI peaks for k=1..K_max,
form the empirical CCDF P(PAoI > x), and report deadline-violation
probabilities and tail quantiles.

Run (on the VM):
    python3 experiments/e_tail.py
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import system as S                 # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def quantile(sorted_vals, q):
    if not sorted_vals:
        return float("nan")
    i = min(len(sorted_vals) - 1, int(q * len(sorted_vals)))
    return sorted_vals[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--W", type=float, default=0.10)
    ap.add_argument("--Ts", type=float, default=0.005)
    ap.add_argument("--eta", type=float, default=6.0, help="energy-abundant")
    ap.add_argument("--B", type=int, default=64)
    ap.add_argument("--Kmax", type=int, default=4)
    ap.add_argument("--ks", type=int, nargs="*", default=[1, 2, 4])
    ap.add_argument("--periods", type=int, default=120000)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.periods, args.seeds = 20000, 3
    os.makedirs(RESULTS, exist_ok=True)

    # grid of deadlines (normalized to P); peaks ~ P + R_min + T_s in [P, P+G]
    grid = [args.P * (1.0 + i / 20.0) for i in range(0, 21)]   # 1.00 .. 2.00 P
    peaks_by_k = {}
    for k in args.ks:
        allpk = []
        for s in range(args.seeds):
            allpk += S.r3_peaks(args.P, args.W, args.Ts, k, args.eta, args.B,
                                args.Kmax, args.periods, seed=7700 + s,
                                warmup_periods=args.warmup)
        peaks_by_k[k] = sorted(allpk)

    # CCDF rows + quantiles
    rows = []
    for x in grid:
        row = {"deadline": round(x, 4)}
        for k in args.ks:
            pk = peaks_by_k[k]
            ccdf = sum(1 for v in pk if v > x) / len(pk)
            row[f"ccdf_k{k}"] = round(ccdf, 5)
        rows.append(row)
    with open(os.path.join(RESULTS, "paoi_ccdf.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    print(f"PAoI tail at eta={args.eta} (normalized to P); n_peaks/k ~ {len(peaks_by_k[args.ks[0]])}")
    print("k   mean    p90     p99    P(PAoI>1.5P)")
    for k in args.ks:
        pk = peaks_by_k[k]
        mean = sum(pk) / len(pk)
        viol = sum(1 for v in pk if v > 1.5 * args.P) / len(pk)
        print(f"{k}  {mean:.3f}  {quantile(pk,0.90):.3f}  {quantile(pk,0.99):.3f}   {viol:.4f}")
    print(f"-> wrote {os.path.join(RESULTS, 'paoi_ccdf.csv')}")


if __name__ == "__main__":
    main()
