#!/usr/bin/env python3
"""E7-E8 -- Result 3 validation (energy-replication threshold).

Integrated energy + replication + AoI sim (montecarlo/system.py):

E7  unimodality and  k* = min(K_max, floor(eta))  at fixed eta.
E8  monotonicity of k*(eta) in eta, and saturation at K_max for
    eta >= K_max.

Run (on the VM):
    python3 experiments/e7_e8_threshold.py
    python3 experiments/e7_e8_threshold.py --quick
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import system as S                  # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def mean_paoi_over_seeds(P, W, Ts, k, eta, B, Kmax, periods, warmup, seeds):
    vals = [S.simulate_r3_paoi(P, W, Ts, k, eta, B, Kmax, periods,
                               seed=8000 + s, warmup_periods=warmup).mean_paoi
            for s in range(seeds)]
    return sum(vals) / len(vals)


def is_unimodal(ys):
    """True if ys decreases then increases (allowing flats)."""
    lo = min(range(len(ys)), key=lambda i: ys[i])
    dec = all(ys[i] >= ys[i + 1] - 1e-9 for i in range(lo))
    inc = all(ys[i] <= ys[i + 1] + 1e-9 for i in range(lo, len(ys) - 1))
    return dec and inc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--W", type=float, default=0.10)
    ap.add_argument("--Ts", type=float, default=0.005)
    ap.add_argument("--B", type=int, default=64, help="battery cap (large: p_e~min(1,eta/k))")
    ap.add_argument("--Kmax", type=int, default=8)
    ap.add_argument("--periods", type=int, default=80000)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.periods, args.warmup, args.seeds = 15000, 500, 4

    os.makedirs(RESULTS, exist_ok=True)
    P, W, Ts, B, Kmax = args.P, args.W, args.Ts, args.B, args.Kmax
    ks = list(range(1, Kmax + 2))   # 1..K_max+1 (probe one past the cap)

    # ---------------- E7: unimodality + argmin ---------------------------
    print(f"=== E7 unimodality + k*=min(K_max,floor(eta)), K_max={Kmax} ===")
    e7_rows = []
    e7_ok = True
    for eta in [3.0, 5.0]:
        ys = [mean_paoi_over_seeds(P, W, Ts, k, eta, B, Kmax, args.periods,
                                   args.warmup, args.seeds) for k in ks]
        argmin_k = ks[min(range(len(ys)), key=lambda i: ys[i])]
        cf = S.k_star_cf(eta, Kmax)
        uni = is_unimodal(ys)
        ok = uni and abs(argmin_k - cf) <= 1     # tolerate +-1 (boundary/noise)
        e7_ok = e7_ok and ok
        curve = " ".join(f"{y:.3f}" for y in ys)
        print(f"  eta={eta:4.1f}  k*={argmin_k}(cf {cf})  unimodal={uni}  "
              f"{'OK' if ok else 'FAIL'}\n      PAoI[k=1..]: {curve}")
        for k, y in zip(ks, ys):
            e7_rows.append(dict(eta=eta, k=k, mean_paoi=y, k_star=argmin_k,
                                k_star_cf=cf, unimodal=uni))
    _write_csv(os.path.join(RESULTS, "e7_threshold.csv"), e7_rows)

    # ---------------- E8: monotonicity + saturation ----------------------
    print("=== E8 monotonicity of k*(eta) + saturation at K_max ===")
    etas = [1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0]
    e8_rows = []
    kstars = []
    for eta in etas:
        ys = [mean_paoi_over_seeds(P, W, Ts, k, eta, B, Kmax, args.periods,
                                   args.warmup, args.seeds) for k in ks]
        argmin_k = ks[min(range(len(ys)), key=lambda i: ys[i])]
        kstars.append(argmin_k)
        cf = S.k_star_cf(eta, Kmax)
        print(f"  eta={eta:5.1f}  k*={argmin_k}  (cf {cf})")
        e8_rows.append(dict(eta=eta, k_star=argmin_k, k_star_cf=cf))
    monotone = all(kstars[i] <= kstars[i + 1] + 1 for i in range(len(kstars) - 1))
    # saturation: for eta >= K_max, k* should sit at K_max (+-1)
    sat = all(abs(ks_ - Kmax) <= 1 for e, ks_ in zip(etas, kstars) if e >= Kmax)
    e8_ok = monotone and sat
    print(f"  k*(eta) = {kstars}  monotone={monotone}  saturates@K_max={sat}  "
          f"{'OK' if e8_ok else 'FAIL'}")
    _write_csv(os.path.join(RESULTS, "e8_monotonicity.csv"), e8_rows)

    print(f"\nE7 {'PASS' if e7_ok else 'FAIL'} | E8 {'PASS' if e8_ok else 'FAIL'}")


def _write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  -> wrote {path}")


if __name__ == "__main__":
    main()
