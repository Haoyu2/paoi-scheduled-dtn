#!/usr/bin/env python3
"""Policy evaluation: AoI-Energy adaptive replication-degree selection.

The policy chooses the replication degree by a closed-form TWO-CANDIDATE
test (O(1), no sweep over k): because A(k) is unimodal with its minimizer
one of the two integers bracketing eta, the policy evaluates A only at
floor(eta) and ceil(eta) and clips to [1,K_max]. A(k) is the mean-PAoI
objective A(k) = P(1-p_e)/p_e + P(1-delta)^{k+1}/(k+1),
p_e=min(1,eta/k). We compare, over an energy sweep:
  - fixed degrees k=1..K_max (simulated PAoI, finite-battery model),
  - the adaptive policy (its PAoI = simulated PAoI at k_policy),
  - the per-eta exhaustive optimum (argmin of simulated PAoI).
Headline: the closed-form policy matches the exhaustive optimum and is the
lower envelope of all fixed-degree curves (adaptive beats any fixed k).

Run (on the VM):
    python3 experiments/e_policy.py
"""
from __future__ import annotations

import argparse
import csv
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


def k_policy(eta, delta, P, Kmax):
    """Closed-form two-candidate optimal degree, O(1).

    A(k) is unimodal with minimizer in {floor(eta), ceil(eta)} (skip-aware
    ceiling test); evaluate only those two and clip to [1, K_max]. No sweep
    over k.
    """
    import math
    lo = min(Kmax, max(1, int(math.floor(eta))))
    hi = min(Kmax, max(1, int(math.ceil(eta))))
    cands = {lo, hi}                     # the two bracketing integers, clipped
    return min(cands, key=lambda k: A_analytic(k, eta, delta, P))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--W", type=float, default=0.10)
    ap.add_argument("--Ts", type=float, default=0.005)
    ap.add_argument("--B", type=int, default=64)
    ap.add_argument("--Kmax", type=int, default=4)
    ap.add_argument("--periods", type=int, default=80000)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.periods, args.seeds = 15000, 4
    os.makedirs(RESULTS, exist_ok=True)
    P, W, Ts, B, Kmax = args.P, args.W, args.Ts, args.B, args.Kmax
    delta = W / P

    etas = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0]
    rows = []
    match = 0
    print(f"K_max={Kmax}, delta={delta}")
    print("eta   PAoI[k=1..K]                         k_pol k_opt  pol==opt")
    for eta in etas:
        paoi = []
        for k in range(1, Kmax + 1):
            vals = [S.simulate_r3_paoi(P, W, Ts, k, eta, B, Kmax, args.periods,
                                       seed=7000 + s, warmup_periods=args.warmup).mean_paoi
                    for s in range(args.seeds)]
            paoi.append(sum(vals) / len(vals))
        kp = k_policy(eta, delta, P, Kmax)
        kopt = 1 + min(range(Kmax), key=lambda i: paoi[i])
        ok = (kp == kopt)
        match += ok
        curve = " ".join(f"{v:.3f}" for v in paoi)
        print(f"{eta:4.1f}  {curve}   {kp}    {kopt}    {'OK' if ok else 'x'}")
        row = dict(eta=eta, k_policy=kp, k_opt=kopt,
                   paoi_policy=paoi[kp - 1], paoi_opt=paoi[kopt - 1])
        for k in range(1, Kmax + 1):
            row[f"paoi_k{k}"] = paoi[k - 1]
        rows.append(row)
    with open(os.path.join(RESULTS, "policy_sweep.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\npolicy == exhaustive optimum in {match}/{len(etas)} cases")
    print(f"-> wrote {os.path.join(RESULTS, 'policy_sweep.csv')}")


if __name__ == "__main__":
    main()
