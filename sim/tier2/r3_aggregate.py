#!/usr/bin/env python3
"""Aggregate the multi-seed R3 raw data into mean +/- 95% CI per (eta, strategy).

Reads results/r3_seeds_raw.csv (eta,strategy,seed,deliv,paoi), writes
results/r3_sweep.csv with CI columns for the figure.

    python3 r3_aggregate.py
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, os.pardir))
from montecarlo.stats import summarize   # noqa: E402

RES = os.path.join(HERE, "results")


def main():
    # CGR-native two-sided comparison: single-copy CGR ('k1') vs CGR k=2 ('cgr2').
    raw, deliv_col = "r3_cgr_raw.csv", "recv"
    strat_map = {"k1": "k1", "cgr2": "k2"}
    by = {}   # (eta, mapped_strat) -> {'deliv':[], 'paoi':[]}
    with open(os.path.join(RES, raw)) as f:
        for r in csv.DictReader(f):
            s = strat_map[r["strategy"]]
            d = by.setdefault((r["eta"], s), {"deliv": [], "paoi": []})
            d["deliv"].append(float(r[deliv_col]))
            d["paoi"].append(float(r["paoi"]))
    etas = sorted({k[0] for k in by}, key=float)
    rows = []
    for eta in etas:
        row = {"eta": eta}
        for s in ("k1", "k2"):
            de, pa = summarize(by[(eta, s)]["deliv"]), summarize(by[(eta, s)]["paoi"])
            row[f"{s}_deliv"] = round(de.mean, 1)
            row[f"{s}_deliv_ci"] = round(de.ci95, 1)
            row[f"{s}_paoi"] = round(pa.mean, 1)
            row[f"{s}_paoi_ci"] = round(pa.ci95, 1)
        rows.append(row)
    out = os.path.join(RES, "r3_sweep.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    nseed = len(by[(rows[0]["eta"], "k1")]["paoi"])
    print(f"wrote {out} ({len(rows)} eta points, n={nseed} seeds each)")
    for r in rows:
        print(f"  eta={r['eta']}  k1_paoi={r['k1_paoi']}+/-{r['k1_paoi_ci']}  "
              f"k2_paoi={r['k2_paoi']}+/-{r['k2_paoi_ci']}  "
              f"k1_deliv={r['k1_deliv']}+/-{r['k1_deliv_ci']}  "
              f"k2_deliv={r['k2_deliv']}+/-{r['k2_deliv_ci']}")


if __name__ == "__main__":
    main()
