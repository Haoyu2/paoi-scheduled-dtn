#!/usr/bin/env python3
"""Aggregate the E17 capacity sweep into results/e17_capacity.csv.

Reads results/e17_capacity_raw.csv
    (k,gen_per_period,window_capacity_m,seed,generated,delivered,copies,
     delay_mean,opaoi)
and writes results/e17_capacity.csv with columns
    k,gen_per_period,window_capacity_m,delivered,delay_mean,opaoi_mean
(means over seeds; delivered = mean distinct updates delivered).

Prints the knee analysis per (k, m): per-window offered copies
(u_win = gpp for k=1 single-relay; ~2*gpp/3 for k=2 diamond), delivery
ratio, and the first offered load where delay inflates >20% above the
low-load (gpp=1.05) baseline.
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def mean(xs):
    return sum(xs) / len(xs)


def main():
    by = defaultdict(lambda: defaultdict(list))
    with open(os.path.join(RES, "e17_capacity_raw.csv")) as f:
        for r in csv.DictReader(f):
            key = (int(r["k"]), float(r["gen_per_period"]),
                   int(r["window_capacity_m"]))
            by[key]["gen"].append(float(r["generated"]))
            by[key]["del"].append(float(r["delivered"]))
            by[key]["delay"].append(float(r["delay_mean"]))
            by[key]["opaoi"].append(float(r["opaoi"]))

    rows = []
    for (k, gpp, m) in sorted(by):
        d = by[(k, gpp, m)]
        rows.append({
            "k": k, "gen_per_period": gpp, "window_capacity_m": m,
            "delivered": round(mean(d["del"]), 1),
            "delay_mean": round(mean(d["delay"]), 1),
            "opaoi_mean": round(mean(d["opaoi"]), 1),
            "_gen": mean(d["gen"]),
        })
    out = os.path.join(RES, "e17_capacity.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "k", "gen_per_period", "window_capacity_m",
            "delivered", "delay_mean", "opaoi_mean"])
        w.writeheader()
        w.writerows([{kk: r[kk] for kk in w.fieldnames} for r in rows])
    print(f"wrote {out}")

    print("\nknee analysis (delay vs offered load; baseline = gpp=1.05):")
    kms = sorted({(r["k"], r["window_capacity_m"]) for r in rows})
    for (k, m) in kms:
        sub = sorted([r for r in rows
                      if r["k"] == k and r["window_capacity_m"] == m],
                     key=lambda r: r["gen_per_period"])
        base = sub[0]["delay_mean"]
        knee = None
        print(f"  k={k} m={m} ({'single relay' if k == 1 else '3-relay diamond'}):")
        for r in sub:
            gpp = r["gen_per_period"]
            uwin = gpp if k == 1 else 2 * gpp / 3   # offered copies per window
            dr = r["delivered"] / r["_gen"]
            infl = r["delay_mean"] / base
            mark = ""
            if knee is None and infl > 1.2:
                knee = gpp
                mark = "   <-- KNEE (delay > 1.2x baseline)"
            print(f"    gpp={gpp:5}  win_copies={uwin:5.2f}/{m}"
                  f"  delivered={dr * 100:6.2f}%"
                  f"  delay={r['delay_mean']:9.1f} ({infl:5.2f}x)"
                  f"  OPAoI={r['opaoi_mean']:9.1f}{mark}")
        print(f"    knee: {'gpp=' + str(knee) if knee else 'none in sweep'}")


if __name__ == "__main__":
    main()
