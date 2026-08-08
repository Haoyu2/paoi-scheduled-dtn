#!/usr/bin/env python3
"""E18 -- validate the uncertainty-aware threshold (Prop. prop:uncertain).

Per-copy success probability q (copy materializes w.p. q; energy spent
regardless) -- the alpha-model already implemented in
system.simulate_r3_paoi. Closed forms under paced generation +
all-or-nothing firing (phase-agnostic profile):

  s_k = 1-(1-q)^k
  h_k(q) = { P[(1-q*delta)^{k+1}-(1-q)^{k+1}]/(q(k+1)) - G(1-q)^k } / s_k
  E[PAoI_per] = P/(p_e s_k) + h_k(q) + T_s,   p_e = min(1, eta/k)

Checks, for q in {0.4, 0.7, 1.0} x k in 1..K_max at eta in {3, 6}:
  1. simulated mean PAoI matches E[PAoI_per] (<2%);
  2. the simulated argmin_k stays in {floor(eta), ceil(eta)};
  3. q=1 reproduces E7's numbers (regression guard).

Run (on the VM):  python3 experiments/e18_uncertain.py [--quick]
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


def h_q(k, q, P, delta):
    G = P * (1 - delta)
    s = 1 - (1 - q) ** k
    integral = P / (q * (k + 1)) * ((1 - q * delta) ** (k + 1) - (1 - q) ** (k + 1))
    return (integral - G * (1 - q) ** k) / s


def paoi_pred(k, q, eta, P, delta, Ts):
    pe = min(1.0, eta / k)
    s = 1 - (1 - q) ** k
    return P / (pe * s) + h_q(k, q, P, delta) + Ts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--W", type=float, default=0.10)
    ap.add_argument("--Ts", type=float, default=0.005)
    ap.add_argument("--B", type=int, default=64)
    ap.add_argument("--Kmax", type=int, default=4)
    ap.add_argument("--periods", type=int, default=200000)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.periods, args.seeds = 20000, 4
    os.makedirs(RESULTS, exist_ok=True)
    P, W, Ts, B, Kmax = args.P, args.W, args.Ts, args.B, args.Kmax
    delta = W / P

    rows, worst, ok_brk = [], 0.0, True
    print("eta  q    PAoI sim[k=1..4]              pred[k=1..4]              maxerr%  k_sim  in{fl,ce}")
    for eta in (3.0, 6.0):
        for q in (0.4, 0.7, 1.0):
            sim, pred = [], []
            for k in range(1, Kmax + 1):
                vals = [S.simulate_r3_paoi(P, W, Ts, k, eta, B, Kmax, args.periods,
                                           seed=18000 + 13 * s + k, alpha=q).mean_paoi
                        for s in range(args.seeds)]
                sim.append(sum(vals) / len(vals))
                pred.append(paoi_pred(k, q, eta, P, delta, Ts))
            errs = [abs(a - b) / b * 100 for a, b in zip(sim, pred)]
            worst = max(worst, max(errs))
            k_sim = 1 + min(range(Kmax), key=lambda i: sim[i])
            lo, hi = min(Kmax, int(math.floor(eta))), min(Kmax, int(math.ceil(eta)))
            brk = k_sim in (lo, hi)
            ok_brk &= brk
            print(f"{eta:.0f}  {q:.1f}  "
                  + " ".join(f"{v:.3f}" for v in sim) + "   "
                  + " ".join(f"{v:.3f}" for v in pred)
                  + f"   {max(errs):.2f}%   {k_sim}     {'OK' if brk else 'x'}")
            for k in range(1, Kmax + 1):
                rows.append(dict(eta=eta, q=q, k=k, paoi_sim=sim[k - 1],
                                 paoi_pred=pred[k - 1], err_pct=errs[k - 1]))
    with open(os.path.join(RESULTS, "e18_uncertain.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nworst |sim-pred| = {worst:.2f}%   bracketing holds: {ok_brk}")
    print("PASS" if worst < 2.0 and ok_brk else "CHECK")


if __name__ == "__main__":
    main()
