#!/usr/bin/env python3
"""Aggregate the E16 unified sweep into results/e16_unified.csv.

Reads results/e16_unified_raw.csv
    (eta,k,seed,opaoi,paoi_per,delay_mean,updates_delivered,
     copies_delivered,admitted,skipped)
and writes results/e16_unified.csv with columns
    eta,k,seeds,opaoi_mean,opaoi_ci,paoi_per_mean,paoi_per_ci,delay_mean,
    delivered_mean,admitted_mean,energy_per_update,success_rate
where energy_per_update = k (atomic admission charges k units per admitted
update) and success_rate = delivered_mean / admitted_mean (delivered =
distinct updates at the destination; under stall-only faults the gap is
horizon-edge stragglers still in transit at sim end).

Also prints the per-eta k-table and argmin_k under BOTH peak metrics, and
the fault-crossover checks: at eta=1 starvation should keep k=1 best; at
eta >= k, replication should now strictly beat k=1 (hedging) -- the
crossover the fault-free atomic experiment (r3_atomic) only tied.
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
    by = defaultdict(lambda: defaultdict(list))
    with open(os.path.join(RES, "e16_unified_raw.csv")) as f:
        for r in csv.DictReader(f):
            key = (float(r["eta"]), int(r["k"]))
            by[key]["opaoi"].append(float(r["opaoi"]))
            by[key]["paoi_per"].append(float(r["paoi_per"]))
            by[key]["delay"].append(float(r["delay_mean"]))
            by[key]["upd"].append(float(r["updates_delivered"]))
            by[key]["adm"].append(float(r["admitted"]))

    etas = sorted({k[0] for k in by})
    ks = sorted({k[1] for k in by})
    rows = []
    for eta in etas:
        for k in ks:
            d = by[(eta, k)]
            om, oc = mstd(d["opaoi"])
            pm, pc = mstd(d["paoi_per"])
            dm, _ = mstd(d["delay"])
            um, _ = mstd(d["upd"])
            am, _ = mstd(d["adm"])
            rows.append({
                "eta": eta, "k": k, "seeds": len(d["opaoi"]),
                "opaoi_mean": round(om, 1), "opaoi_ci": round(oc, 1),
                "paoi_per_mean": round(pm, 1), "paoi_per_ci": round(pc, 1),
                "delay_mean": round(dm, 1),
                "delivered_mean": round(um, 1), "admitted_mean": round(am, 1),
                "energy_per_update": k,
                "success_rate": round(um / am, 4) if am else float("nan"),
            })
    out = os.path.join(RES, "e16_unified.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}")

    om = {(r["eta"], r["k"]): r["opaoi_mean"] for r in rows}
    pm = {(r["eta"], r["k"]): r["paoi_per_mean"] for r in rows}
    print("\nper-eta table (mean over seeds):")
    for eta in etas:
        for name, m in (("OPAoI", om), ("PAoI/reset", pm)):
            vals = {k: m[(eta, k)] for k in ks}
            amin = min(vals, key=vals.get)
            print(f"  eta={eta} {name:10s}: "
                  + "  ".join(f"k={k}:{vals[k]:9.1f}" for k in ks)
                  + f"   argmin={amin}")

    def chk(name, ok):
        print(f"{name}: {'PASS' if ok else 'FAIL'}")

    print("\nfault-crossover checks (OPAoI):")
    if all((1.0, k) in om for k in (1, 2, 3)):
        chk("(i) eta=1: starvation keeps k=1 best (k1 < k2 < k3)",
            om[(1.0, 1)] < om[(1.0, 2)] < om[(1.0, 3)])
    for eta in (2.0, 3.0, 6.0):
        if eta in etas:
            repl = [om[(eta, k)] for k in ks
                    if k >= 2 and k <= eta and (eta, k) in om]
            if repl:
                chk(f"(ii) eta={eta}: some k in [2,eta] beats k=1 (hedging)",
                    min(repl) < om[(eta, 1)])
    argmins = [min(ks, key=lambda k: om[(eta, k)]) for eta in etas]
    chk("(iii) argmin_k non-decreasing in eta",
        all(a <= b for a, b in zip(argmins, argmins[1:])))
    crossed = any(a >= 2 for a in argmins)
    chk("(iv) crossover exists (argmin moves off k=1 somewhere)", crossed)
    print("argmins (OPAoI):", dict(zip(etas, argmins)))


if __name__ == "__main__":
    main()
