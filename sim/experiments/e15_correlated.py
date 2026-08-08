#!/usr/bin/env python3
"""E15 (D): robustness of the energy-replication threshold to CORRELATED
(bursty) harvest.

The i.i.d.-harvest assumption is the most idealized piece of Result 3. Here
the per-period harvest is Markov-modulated: a 2-state chain (hi/lo) with
persistence phi (P[stay] = phi), harvest A ~ Poisson(1.5*eta) in hi and
Poisson(0.5*eta) in lo -- stationary mean eta, mean dwell 1/(1-phi) periods.

Claims tested (eta = 3, K_max = 6, B = 64):
  1. work conservation k*p_e = eta - L is DISTRIBUTION-FREE (Lemma lem:work
     is a flow balance -- it must survive correlation);
  2. the PAoI-optimal degree stays k* = 3 = floor(eta) for all phi
     (the threshold depends on the mean, not the burst structure);
  3. what correlation DOES change: the skip-gap variance, i.e. the PAoI
     tail (p99) inflates with phi while the mean barely moves.

Run (on the VM):
    python3 experiments/e15_correlated.py            # full
    python3 experiments/e15_correlated.py --quick
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo.battery import poisson                 # noqa: E402
from montecarlo.residual import residual               # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def simulate(P, W, Ts, k, eta, B, K_max, phi, n_periods, seed, warmup=1000):
    """Like system.simulate_r3_paoi but with 2-state Markov-modulated harvest.
    Returns (mean_paoi, p99_paoi, p_e, wc_err) where wc_err = |k*p_e-(eta-L)|."""
    rng = random.Random(seed)
    kc = min(k, K_max)
    hi = rng.random() < 0.5
    b = 0
    last_n = None
    fires = counted = 0
    peaks = []
    lost = 0.0          # harvest lost to the battery cap (measures L)
    harvested = 0.0
    for n in range(n_periods):
        fired = b >= k
        if fired:
            b -= k
        # Markov-modulated harvest
        if rng.random() > phi:
            hi = not hi
        A = poisson(rng, 1.5 * eta if hi else 0.5 * eta)
        if n >= warmup:
            harvested += A
            lost += max(0, b + A - B)
        b = min(B, b + A)
        if n < warmup:
            if fired:
                last_n = n
            continue
        counted += 1
        if fired:
            fires += 1
            rmin = min(residual(rng.uniform(0.0, P), P, W) for _ in range(kc))
            if last_n is not None:
                peaks.append((n - last_n) * P + rmin + Ts)
            last_n = n
    p_e = fires / counted
    L = lost / counted
    eta_real = harvested / counted
    wc_err = abs(k * p_e - (eta_real - L))
    peaks.sort()
    mean = sum(peaks) / len(peaks)
    p99 = peaks[int(0.99 * len(peaks))]
    return mean, p99, p_e, wc_err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--P", type=float, default=1.0)
    ap.add_argument("--W", type=float, default=0.10)
    ap.add_argument("--Ts", type=float, default=0.005)
    ap.add_argument("--eta", type=float, default=3.0)
    ap.add_argument("--B", type=int, default=64)
    ap.add_argument("--Kmax", type=int, default=6)
    ap.add_argument("--periods", type=int, default=200000)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.periods, args.seeds = 20000, 4
    os.makedirs(RESULTS, exist_ok=True)
    P, W, Ts, eta, B, Kmax = args.P, args.W, args.Ts, args.eta, args.B, args.Kmax

    phis = [0.0, 0.9, 0.98]
    rows = []
    ok_k = ok_wc = True
    print(f"eta={eta}, B={B}, K_max={Kmax}  (phi=0 -> i.i.d.; dwell=1/(1-phi))")
    print("phi   PAoI[k=1..6]                                    k*  p99(k*)  max_wc_err")
    for phi in phis:
        means, p99s, wcs = [], [], []
        for k in range(1, Kmax + 1):
            ms, ps, ws = [], [], []
            for s in range(args.seeds):
                m, p99, pe, wc = simulate(P, W, Ts, k, eta, B, Kmax, phi,
                                          args.periods, seed=15000 + 97 * s + k)
                ms.append(m); ps.append(p99); ws.append(wc)
            means.append(sum(ms) / len(ms))
            p99s.append(sum(ps) / len(ps))
            wcs.append(max(ws))
        kstar = 1 + min(range(Kmax), key=lambda i: means[i])
        ok_k &= (kstar == 3)
        ok_wc &= max(wcs) < 5e-3
        curve = " ".join(f"{v:.3f}" for v in means)
        print(f"{phi:.2f}  {curve}   {kstar}   {p99s[kstar-1]:.3f}   {max(wcs):.1e}")
        rows.append(dict(phi=phi, k_star=kstar, p99_at_kstar=p99s[kstar - 1],
                         max_wc_err=max(wcs),
                         **{f"paoi_k{k}": means[k - 1] for k in range(1, Kmax + 1)},
                         **{f"p99_k{k}": p99s[k - 1] for k in range(1, Kmax + 1)}))
    with open(os.path.join(RESULTS, "e15_correlated.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nk* = 3 under all phi: {ok_k};  work conservation holds: {ok_wc}")
    print(f"-> wrote {os.path.join(RESULTS, 'e15_correlated.csv')}")
    print("PASS" if ok_k and ok_wc else "CHECK")


if __name__ == "__main__":
    main()
