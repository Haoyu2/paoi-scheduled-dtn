#!/usr/bin/env python3
"""Numerical verification of the uncertainty increment condition
(eq:gainboundq) and the clipped two-candidate property of Prop. 1.

Pure closed-form arithmetic (no simulation): sweeps
    delta in [0.02, 0.9] x q in [0.05, 1] x eta in [0.1, 8]
and reports (a) the minimum margin of
    (P/eta) * Delta_k(k/s_k)  >=  h_k(q) - h_{k+1}(q),  k >= ceil(eta),
and (b) whether argmin_k A_q(k) stays in the clipped candidate set
{max(1, floor(eta)), max(1, ceil(eta))} at every grid point.

Run:  python3 experiments/check_gainboundq.py
"""
from __future__ import annotations

import math


def h_q(k: int, q: float, P: float, d: float) -> float:
    G = P * (1 - d)
    s = 1 - (1 - q) ** k
    return (P / (q * (k + 1)) * ((1 - q * d) ** (k + 1) - (1 - q) ** (k + 1))
            - G * (1 - q) ** k) / s


def cond_margin(q: float, eta: float, d: float, P: float = 1.0,
                kmax: int = 12) -> float:
    ce = max(1, math.ceil(eta))
    m = float("inf")
    for k in range(ce, kmax):
        s_k = 1 - (1 - q) ** k
        s_k1 = 1 - (1 - q) ** (k + 1)
        dphi = (k + 1) / s_k1 - k / s_k
        m = min(m, P / eta * dphi - (h_q(k, q, P, d) - h_q(k + 1, q, P, d)))
    return m


def brackets_ok(q: float, eta: float, d: float, P: float = 1.0,
                kmax: int = 12) -> bool:
    vals = {}
    for k in range(1, kmax + 1):
        pe = min(1.0, eta / k)
        s = 1 - (1 - q) ** k
        vals[k] = P * (1 - pe * s) / (pe * s) + h_q(k, q, P, d)
    kopt = min(vals, key=vals.get)
    return kopt in (max(1, math.floor(eta)), max(1, math.ceil(eta)))


def main() -> None:
    worst, worst_at, bad, n = float("inf"), None, 0, 0
    for d in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9):
        for q in (0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0):
            for eta in (0.1, 0.3, 0.5, 0.7, 1.0, 1.3, 1.7, 2.0, 2.5,
                        3.0, 3.5, 4.0, 5.0, 6.0, 8.0):
                n += 1
                m = cond_margin(q, eta, d)
                if m < worst:
                    worst, worst_at = m, (d, q, eta)
                if not brackets_ok(q, eta, d):
                    bad += 1
                    print("BRACKET MISS", d, q, eta)
    print(f"grid points: {n}")
    print(f"condition minimum margin: {worst:.6f} P at (delta,q,eta)={worst_at}")
    print(f"bracket misses (candidate set clipped to [1,..]): {bad}")
    print("PASS" if bad == 0 and worst > 0 else "CHECK")


if __name__ == "__main__":
    main()
