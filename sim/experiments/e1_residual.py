#!/usr/bin/env python3
"""E1 / E2 -- Result 1 validation (residual law + AoI/PAoI + provisioning).

E1  residual law:  mixed atom+slab; E[R], E[R^2] match closed form;
    empirical atom fraction ~ delta; KS to mixed CDF small.
E2  provisioning divergence: log-log slope of the *gating* part of mean
    AoI is ~2 in (1-delta); of PAoI is ~1.

Run (on the VM):
    python3 experiments/e1_residual.py                 # full defaults
    python3 experiments/e1_residual.py --quick          # fast smoke
    python3 experiments/e1_residual.py --periods 4000 --lam 400 --seeds 30

Time is normalized to P = 1 (results are dimensionless ratios; the
real-seconds anchor lives in scenarios/leo_single.yaml). Output CSVs are
written to sim/results/.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import residual as R          # noqa: E402
from montecarlo.stats import summarize         # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

DEFAULT_DELTAS = [0.02, 0.05, 0.075, 0.10, 0.20, 0.35, 0.50]


def ols_slope(xs, ys):
    """Least-squares slope of ys vs xs."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else float("nan")


def main():
    ap = argparse.ArgumentParser(description="E1/E2 residual + AoI/PAoI validation")
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--Ts", type=float, default=0.005, help="service+prop (<< P)")
    ap.add_argument("--lam", type=float, default=300.0, help="Poisson gen rate")
    ap.add_argument("--periods", type=int, default=1000)
    ap.add_argument("--warmup", type=int, default=100)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--nsamp", type=int, default=200000, help="residual samples/seed")
    ap.add_argument("--quick", action="store_true", help="fast smoke settings")
    ap.add_argument("--deltas", type=float, nargs="*", default=DEFAULT_DELTAS)
    args = ap.parse_args()

    if args.quick:
        args.periods, args.warmup, args.seeds = 100, 10, 5
        args.lam, args.nsamp = 50.0, 20000

    os.makedirs(RESULTS, exist_ok=True)
    P, Ts, lam = args.P, args.Ts, args.lam

    # ---------------- E1: residual law -----------------------------------
    print("=== E1 residual law ===")
    e1_rows = []
    e1_pass = True
    for delta in args.deltas:
        W = delta * P
        means, sqs, kss, atoms = [], [], [], []
        for s in range(args.seeds):
            rs = R.sample_residuals(P, W, args.nsamp, seed=1000 + s)
            means.append(rs.mean); sqs.append(rs.mean_sq)
            kss.append(rs.ks_stat); atoms.append(rs.atom_frac)
        em, esq = summarize(means), summarize(sqs)
        eks, eat = summarize(kss), summarize(atoms)
        cf_m, cf_sq = R.mean_residual_cf(P, W), R.mean_sq_residual_cf(P, W)
        ok = em.contains(cf_m) and esq.contains(cf_sq) and eks.mean < 0.02 \
            and abs(eat.mean - delta) < 0.01
        e1_pass = e1_pass and ok
        print(f"  delta={delta:5.3f}  E[R]={em} cf={cf_m:.5g}  "
              f"KS={eks.mean:.4f}  atom={eat.mean:.4f}(cf {delta})  {'OK' if ok else 'FAIL'}")
        e1_rows.append(dict(delta=delta, mean_R=em.mean, mean_R_ci=em.ci95,
                            mean_R_cf=cf_m, meanSq_R=esq.mean, meanSq_R_cf=cf_sq,
                            ks=eks.mean, atom=eat.mean, passed=ok))
    _write_csv(os.path.join(RESULTS, "e1_residual.csv"), e1_rows)

    # ---------------- E2: AoI/PAoI + provisioning slopes ------------------
    print("=== E2 AoI / PAoI + provisioning slopes ===")
    e2_rows = []
    gate_aoi, gate_paoi, log_1md = [], [], []
    for delta in args.deltas:
        W = delta * P
        aoi_s, paoi_s = [], []
        for s in range(args.seeds):
            run = R.simulate_aoi(P, W, Ts, lam, args.periods, args.warmup,
                                 seed=2000 + s)
            aoi_s.append(run.mean_aoi); paoi_s.append(run.paoi)
        ea, ep = summarize(aoi_s), summarize(paoi_s)
        cf_a, cf_p = R.mean_aoi_cf(P, W, Ts), R.paoi_cf(P, W, Ts)
        # compare the gating part (metric - T_s): the part the theory governs
        gate_a_cf, gate_p_cf = cf_a - Ts, cf_p - Ts
        rel_a = abs((ea.mean - Ts) - gate_a_cf) / gate_a_cf
        rel_p = abs((ep.mean - Ts) - gate_p_cf) / gate_p_cf
        ok = rel_a < 0.06 and rel_p < 0.06
        print(f"  delta={delta:5.3f}  AoI={ea.mean:.5g} cf={cf_a:.5g} (gate {rel_a*100:.1f}%) | "
              f"PAoI={ep.mean:.5g} cf={cf_p:.5g} (gate {rel_p*100:.1f}%)  {'OK' if ok else 'FAIL'}")
        e2_rows.append(dict(delta=delta, aoi=ea.mean, aoi_ci=ea.ci95, aoi_cf=cf_a,
                            paoi=ep.mean, paoi_ci=ep.ci95, paoi_cf=cf_p, passed=ok))
        # gating part = metric - T_s ; slope vs log(1-delta)
        log_1md.append(math.log(1.0 - delta))
        gate_aoi.append(math.log(max(ea.mean - Ts, 1e-12)))
        gate_paoi.append(math.log(max(ep.mean - Ts, 1e-12)))
    slope_aoi = ols_slope(log_1md, gate_aoi)
    slope_paoi = ols_slope(log_1md, gate_paoi)
    slope_ok = abs(slope_aoi - 2.0) < 0.1 and abs(slope_paoi - 1.0) < 0.1
    print(f"  provisioning slopes: mean-AoI={slope_aoi:.3f} (cf 2), "
          f"PAoI={slope_paoi:.3f} (cf 1)  {'OK' if slope_ok else 'FAIL'}")
    _write_csv(os.path.join(RESULTS, "e2_aoi_paoi.csv"), e2_rows)

    print(f"\nE1 {'PASS' if e1_pass else 'FAIL'} | "
          f"E2 slopes {'PASS' if slope_ok else 'FAIL'}")


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
