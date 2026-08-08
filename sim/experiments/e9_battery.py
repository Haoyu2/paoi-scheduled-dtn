#!/usr/bin/env python3
"""E9 / E10 -- sec 6.4 battery-queue throttle validation.

E9  work conservation:  k*p_e = eta - L  (so p_e <= min(1, eta/k)),
    and distribution-free: Poisson vs deterministic harvest agree.
E10 k=1, large B, eta<1:  p_e = eta  and  P(b=0) = 1 - eta (M/D/1 limit).

Run (on the VM):
    python3 experiments/e9_battery.py
    python3 experiments/e9_battery.py --quick
    python3 experiments/e9_battery.py --periods 500000 --seeds 30
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import battery as B            # noqa: E402
from montecarlo.stats import summarize          # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def _run_grid(ks, etas, Bcap, periods, warmup, seeds, harvest):
    rows = []
    all_ok = True
    for k in ks:
        for eta in etas:
            pes, ress, ovs = [], [], []
            for s in range(seeds):
                r = B.simulate_battery(Bcap, k, eta, periods, seed=3000 + s,
                                       warmup_periods=warmup, harvest=harvest)
                pes.append(r.p_e)
                ress.append(r.work_conservation_residual(k))
                ovs.append(r.overflow_L)
            epe, eres, eov = summarize(pes), summarize(ress), summarize(ovs)
            fluid = B.p_e_fluid(k, eta)
            wc_ok = eres.mean < 1e-2                       # identity holds
            bound_ok = epe.mean <= fluid + epe.ci95 + 1e-9  # p_e <= min(1,eta/k)
            ok = wc_ok and bound_ok
            all_ok = all_ok and ok
            print(f"  [{harvest:>13}] k={k} eta={eta:5.2f}  "
                  f"p_e={epe.mean:.4f}+/-{epe.ci95:.3g} (<= {fluid:.4f})  "
                  f"L={eov.mean:.4f}  |WC|={eres.mean:.2e}  {'OK' if ok else 'FAIL'}")
            rows.append(dict(harvest=harvest, k=k, eta=eta, p_e=epe.mean,
                             p_e_ci=epe.ci95, p_e_fluid=fluid, overflow_L=eov.mean,
                             wc_residual=eres.mean, passed=ok))
    return rows, all_ok


def main():
    ap = argparse.ArgumentParser(description="E9/E10 battery-queue validation")
    ap.add_argument("--B", type=int, default=64, help="battery capacity (units)")
    ap.add_argument("--periods", type=int, default=200000)
    ap.add_argument("--warmup", type=int, default=2000)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    if args.quick:
        args.periods, args.warmup, args.seeds = 20000, 500, 5

    os.makedirs(RESULTS, exist_ok=True)

    print("=== E9 work conservation (Poisson harvest) ===")
    ks = [1, 2, 3, 4]
    etas = [0.5, 1.0, 2.0, 3.0, 5.0]
    rows_p, ok_p = _run_grid(ks, etas, args.B, args.periods, args.warmup,
                             args.seeds, "poisson")
    print("=== E9 distribution-free check (deterministic harvest) ===")
    rows_d, ok_d = _run_grid([2, 3], [1.0, 2.0, 3.0], args.B, args.periods,
                             args.warmup, args.seeds, "deterministic")
    _write_csv(os.path.join(RESULTS, "e9_work_conservation.csv"), rows_p + rows_d)

    # ---------------- E10: k=1 M/D/1 limit -------------------------------
    print("=== E10  k=1 large-B limit:  p_e=eta, P(b=0)=1-eta ===")
    e10_rows = []
    ok_10 = True
    bigB = max(args.B, 256)
    for eta in [0.3, 0.5, 0.7, 0.9]:
        pes, p0s = [], []
        for s in range(args.seeds):
            r = B.simulate_battery(bigB, 1, eta, args.periods, seed=4000 + s,
                                   warmup_periods=args.warmup, harvest="poisson")
            pes.append(r.p_e); p0s.append(r.p_zero)
        epe, ep0 = summarize(pes), summarize(p0s)
        ok = epe.rel_error(eta) < 0.03 and ep0.rel_error(1 - eta) < 0.03
        ok_10 = ok_10 and ok
        print(f"  eta={eta:4.2f}  p_e={epe.mean:.4f}(cf {eta})  "
              f"P(b=0)={ep0.mean:.4f}(cf {1-eta:.2f})  {'OK' if ok else 'FAIL'}")
        e10_rows.append(dict(eta=eta, p_e=epe.mean, p_e_cf=eta,
                             p_zero=ep0.mean, p_zero_cf=1 - eta, passed=ok))
    _write_csv(os.path.join(RESULTS, "e10_md1_limit.csv"), e10_rows)

    print(f"\nE9 Poisson {'PASS' if ok_p else 'FAIL'} | "
          f"E9 deterministic {'PASS' if ok_d else 'FAIL'} | "
          f"E10 {'PASS' if ok_10 else 'FAIL'}")


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
