#!/usr/bin/env python3
"""Aggregate the atomic-admission sweep into results/r3_atomic.csv.

Reads results/r3_atomic_raw.csv (eta,k,seed,paoi,updates_delivered,
copies_delivered), writes results/r3_atomic.csv with columns
eta,k,seeds,paoi_mean,paoi_ci,delivered_mean (delivered = distinct
updates delivered after dedup by generation time; ci = 95% normal CI).
Also prints the pass-criteria checks (over-replication penalty ordering
at low eta, ordering at high eta, argmin trajectory).
"""
import csv
import math
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def mstd(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    return m, 1.96 * sd / math.sqrt(n) if n > 1 else 0.0


def main():
    by = defaultdict(lambda: {"paoi": [], "upd": []})
    with open(os.path.join(RES, "r3_atomic_raw.csv")) as f:
        for r in csv.DictReader(f):
            key = (float(r["eta"]), int(r["k"]))
            by[key]["paoi"].append(float(r["paoi"]))
            by[key]["upd"].append(float(r["updates_delivered"]))

    etas = sorted({k[0] for k in by})
    ks = sorted({k[1] for k in by})
    rows = []
    for eta in etas:
        for k in ks:
            pm, pc = mstd(by[(eta, k)]["paoi"])
            um, _ = mstd(by[(eta, k)]["upd"])
            rows.append({"eta": eta, "k": k, "seeds": len(by[(eta, k)]["paoi"]),
                         "paoi_mean": round(pm, 1), "paoi_ci": round(pc, 1),
                         "delivered_mean": round(um, 1)})
    out = os.path.join(RES, "r3_atomic.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}")

    pm = {(r["eta"], r["k"]): r["paoi_mean"] for r in rows}
    for eta in etas:
        vals = {k: pm[(eta, k)] for k in ks}
        amin = min(vals, key=vals.get)
        ties = sorted(k for k in ks if vals[k] <= vals[amin] * 1.02)
        print(f"eta={eta}: " + "  ".join(f"k={k}:{vals[k]}" for k in ks)
              + f"   argmin={amin} (within2%:{ties})")

    def chk(name, ok):
        print(f"{name}: {'PASS' if ok else 'FAIL'}")

    for eta in (0.6, 1.0):
        if eta in etas:
            chk(f"(i) eta={eta} strict k1<k2<k3",
                pm[(eta, 1)] < pm[(eta, 2)] < pm[(eta, 3)])
    for eta in (3.0, 6.0):
        if eta in etas:
            chk(f"(ii) eta={eta} k3<=k2<=k1",
                pm[(eta, 3)] <= pm[(eta, 2)] <= pm[(eta, 1)])
    argmins = [min(ks, key=lambda k: pm[(eta, k)]) for eta in etas]
    chk("(iii) argmin non-decreasing in eta",
        all(a <= b for a, b in zip(argmins, argmins[1:])))
    print("argmins:", dict(zip(etas, argmins)))


if __name__ == "__main__":
    main()
