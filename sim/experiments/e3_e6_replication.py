#!/usr/bin/env python3
"""E3-E6 -- Result 2 validation (phase mixing + order-statistic gain).

E3  phase-mixing lemma: incommensurate periods -> downstream phase
    uniform and decoupled from upstream; commensurate periods -> locked.
E4  k=2 gain: E[R]-E[R_min] = (1/2)E|R1-R2|; E[R_min]=G^3/3P^2;
    ratio E[R_min]/E[R] = (2/3)(1-delta).
E5  same-bottleneck copies -> gain ~ 0.
E6  windows staggered by P/2 -> worst-case residual ~ P/2 - W.

Run (on the VM):
    python3 experiments/e3_e6_replication.py            # defaults
    python3 experiments/e3_e6_replication.py --quick
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import multihop as M               # noqa: E402
from montecarlo.stats import summarize              # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
DEFAULT_DELTAS = [0.02, 0.05, 0.10, 0.20, 0.35, 0.50]
PHI = 0.6180339887498949   # 1/golden ratio: strongly incommensurate with 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--W", type=float, default=0.10)
    ap.add_argument("--T1", type=float, default=0.01)
    ap.add_argument("--npkt", type=int, default=200000)
    ap.add_argument("--nsamp", type=int, default=400000)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--deltas", type=float, nargs="*", default=DEFAULT_DELTAS)
    args = ap.parse_args()
    if args.quick:
        args.npkt, args.nsamp, args.seeds = 20000, 40000, 4

    os.makedirs(RESULTS, exist_ok=True)
    P, W, T1 = args.P, args.W, args.T1

    # ---------------- E3: phase mixing -----------------------------------
    print("=== E3 phase-mixing lemma ===")
    cases = [("incommensurate", PHI), ("equal(P2=P1)", P), ("rational(2:1)", P / 2)]
    e3_rows = []
    e3_ok = True
    for label, P2 in cases:
        kss, corrs = [], []
        for s in range(args.seeds):
            r = M.two_hop_phase(P, W, T1, P2, W, args.npkt, seed=5000 + s)
            kss.append(r.ks_uniform); corrs.append(abs(r.corr_R2_D1))
        eks, ecorr = summarize(kss), summarize(corrs)
        if label.startswith("incomm"):
            ok = eks.mean < 0.03 and ecorr.mean < 0.05      # mixing holds
        else:
            ok = eks.mean > 0.10 or ecorr.mean > 0.10        # locking detected
        e3_ok = e3_ok and ok
        print(f"  {label:16}  KS(uniform)={eks.mean:.4f}  |corr(R2,D1)|={ecorr.mean:.4f}  "
              f"{'OK' if ok else 'FAIL'}")
        e3_rows.append(dict(case=label, P2=P2, ks_uniform=eks.mean,
                            corr_abs=ecorr.mean, passed=ok))
    _write_csv(os.path.join(RESULTS, "e3_phase_mixing.csv"), e3_rows)

    # ---------------- E4/E5/E6: order-statistic gain ---------------------
    print("=== E4 k=2 order-statistic gain (Gini identity + ratio) ===")
    e4_rows = []
    e4_ok = True
    for delta in args.deltas:
        Wd = delta * P
        gains, halfs, rmins, ratios = [], [], [], []
        for s in range(args.seeds):
            g = M.two_copy_gain(P, Wd, args.nsamp, seed=6000 + s)
            gains.append(g.mean_R - g.mean_Rmin)
            halfs.append(g.half_mean_absdiff)
            rmins.append(g.mean_Rmin)
            ratios.append(g.ratio_min_over_R)
        eg, eh, erm, erat = (summarize(gains), summarize(halfs),
                             summarize(rmins), summarize(ratios))
        cf_rmin = M.residual_min_cf(P, Wd, 2)
        cf_ratio = (2.0 / 3.0) * (1 - delta)
        ok = (abs(eg.mean - eh.mean) < 2 * (eg.ci95 + eh.ci95) + 1e-6
              and erm.rel_error(cf_rmin) < 0.03
              and erat.rel_error(cf_ratio) < 0.03)
        e4_ok = e4_ok and ok
        print(f"  delta={delta:5.3f}  gain={eg.mean:.5g} vs 1/2 E|dR|={eh.mean:.5g} | "
              f"E[Rmin]={erm.mean:.5g}(cf {cf_rmin:.5g}) | "
              f"ratio={erat.mean:.4f}(cf {cf_ratio:.4f})  {'OK' if ok else 'FAIL'}")
        e4_rows.append(dict(delta=delta, gain=eg.mean, half_absdiff=eh.mean,
                            mean_Rmin=erm.mean, Rmin_cf=cf_rmin,
                            ratio=erat.mean, ratio_cf=cf_ratio, passed=ok))
    _write_csv(os.path.join(RESULTS, "e4_k2_gain.csv"), e4_rows)

    print("=== E5 same-bottleneck copies -> gain ~ 0 ===")
    e5_ok = True
    for delta in [0.05, 0.20, 0.50]:
        Wd = delta * P
        gains = []
        for s in range(args.seeds):
            g = M.two_copy_gain(P, Wd, args.nsamp, seed=6500 + s, same_bottleneck=True)
            gains.append(g.mean_R - g.mean_Rmin)
        eg = summarize(gains)
        ok = abs(eg.mean) < 1e-9
        e5_ok = e5_ok and ok
        print(f"  delta={delta:5.3f}  gain={eg.mean:.3e}  {'OK' if ok else 'FAIL'}")

    print("=== E6 P/2 staggering -> worst-case residual ~ P/2 - W ===")
    e6_ok = True
    for delta in [0.05, 0.10, 0.20]:
        Wd = delta * P
        worst = max(M.staggered_max_residual(P, Wd, args.nsamp, seed=7000 + s)
                    for s in range(args.seeds))
        target = P / 2 - Wd
        single = P - Wd
        ok = abs(worst - target) < 0.02 * P
        e6_ok = e6_ok and ok
        print(f"  delta={delta:5.3f}  max R_min={worst:.4f}  target P/2-W={target:.4f}  "
              f"(single-sat G={single:.3f})  {'OK' if ok else 'FAIL'}")

    print(f"\nE3 {'PASS' if e3_ok else 'FAIL'} | E4 {'PASS' if e4_ok else 'FAIL'} | "
          f"E5 {'PASS' if e5_ok else 'FAIL'} | E6 {'PASS' if e6_ok else 'FAIL'}")


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
