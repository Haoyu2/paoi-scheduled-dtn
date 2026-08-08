#!/usr/bin/env python3
"""CGR-UCoP (RUCoP MDP) comparison vs the AoI-Energy policy.

(1) Validates the RUCoP MDP solver: on a symmetric diamond it must match
    the closed form 1-(1-q)^k; on a multi-hop mesh it solves a non-trivial
    forwarding MDP.
(2) Compares three policies on a heterogeneous uncertain diamond:
      - single-copy CGR (k=1),
      - AoI-Energy policy (k = k*(eta), energy-aware),
      - RUCoP (delivery-optimal, energy-blind: k = K_max),
    on delivery probability and energy (copies/update). RUCoP maximizes
    delivery but over-spends energy on the concave tail; our policy sits on
    the efficient frontier.

Run (on the VM):
    python3 experiments/e_rucop.py
"""
from __future__ import annotations

import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import rucop as R                  # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def diamond(qs, source=0, dest=1):
    """Bent-pipe diamond: each relay path collapses to one uncertain
    source->dest super-edge with success prob q_i (relay up w.p. q_i).
    A copy committed to path i costs one source transmission. Returns
    (contacts, source, dest)."""
    contacts = [(source, dest, q) for q in qs]
    return contacts, source, dest


def mesh():
    """Small multi-hop mesh where forwarding decisions interact (non-trivial MDP).
    0=src, 1,2=tier1, 3=mid, 4=dest."""
    c = [(0, 1, 0.6), (0, 2, 0.6),
         (1, 3, 0.8), (2, 3, 0.8),
         (1, 4, 0.5), (2, 4, 0.5),
         (3, 4, 0.9)]
    return c, 0, 4


def main():
    os.makedirs(RESULTS, exist_ok=True)

    # ---- (1) validate the DP --------------------------------------------
    print("=== RUCoP DP validation ===")
    q = 0.7
    K = 5
    contacts, s, d = diamond([q] * K)
    ok = True
    for k in range(1, K + 1):
        got = R.delivery_prob(contacts, s, d, k)
        cf = 1 - (1 - q) ** k
        good = abs(got - cf) < 1e-9
        ok = ok and good
        print(f"  symmetric diamond k={k}: DP={got:.5f} cf={cf:.5f} {'OK' if good else 'FAIL'}")
    cm, sm, dm = mesh()
    print("  mesh delivery(k):", [round(R.delivery_prob(cm, sm, dm, k), 4) for k in range(1, 5)],
          "(monotone, non-trivial MDP)")
    print(f"  DP validation {'PASS' if ok else 'FAIL'}")

    # ---- (2) comparison on a heterogeneous diamond ----------------------
    qs = [0.80, 0.70, 0.60, 0.50, 0.40]      # heterogeneous relay availabilities
    K = len(qs)
    contacts, s, d = diamond(qs)
    deliv = {k: R.delivery_prob(contacts, s, d, k) for k in range(1, K + 1)}
    print("\n=== heterogeneous diamond: RUCoP delivery(k) frontier ===")
    for k in range(1, K + 1):
        print(f"  k={k}: delivery={deliv[k]:.4f}  (energy={k} copies/update)")

    # policies across an energy sweep (eta); K_max = K
    rows = []
    print("\neta  single(k=1)         AoI-Energy(k*)        RUCoP(k=K)")
    for eta in [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]:
        kstar = max(1, min(K, int(math.floor(eta))))
        k_ruc = K                                  # delivery-optimal, energy-blind
        row = dict(eta=eta,
                   single_k=1, single_deliv=round(deliv[1], 4), single_energy=1,
                   ours_k=kstar, ours_deliv=round(deliv[kstar], 4), ours_energy=kstar,
                   rucop_k=k_ruc, rucop_deliv=round(deliv[k_ruc], 4), rucop_energy=k_ruc)
        rows.append(row)
        print(f"{eta:4.1f}  d={deliv[1]:.3f} e=1        "
              f"k*={kstar} d={deliv[kstar]:.3f} e={kstar}      "
              f"k={k_ruc} d={deliv[k_ruc]:.3f} e={k_ruc}")

    # frontier csv (delivery vs energy) for the figure
    with open(os.path.join(RESULTS, "rucop_frontier.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["k", "delivery", "energy"])
        w.writeheader()
        for k in range(1, K + 1):
            w.writerow({"k": k, "delivery": round(deliv[k], 5), "energy": k})
    with open(os.path.join(RESULTS, "rucop_compare.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # efficiency headline: ours vs RUCoP at a constrained energy
    e2 = deliv[2] / deliv[K]
    print(f"\nAt k*=2 ours achieves {e2*100:.1f}% of RUCoP's delivery "
          f"using {2}/{K} = {2/K*100:.0f}% of the energy.")
    print(f"-> wrote rucop_frontier.csv, rucop_compare.csv")


if __name__ == "__main__":
    main()
