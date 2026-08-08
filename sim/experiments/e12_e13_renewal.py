#!/usr/bin/env python3
"""E13 + E12 -- sec 6.5 renewal residual law and AoI/PAoI inversion.

E13 residual law across segment types: mean R = E[V^2]/(2E[C]), atom =
    U/E[C]; deterministic gap recovers Result 1.
E12 inversion: sweep gap CV (fixed mean); mean PAoI < mean AoI iff
    E[V^2] > 2E[C]E[V] (-> CV^2 > 1). LEO/jitter no inversion; heavy-tailed
    terrestrial inverts.

Run (on the VM):
    python3 experiments/e12_e13_renewal.py
    python3 experiments/e12_e13_renewal.py --quick
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from montecarlo import renewal as RN                 # noqa: E402
from montecarlo.stats import summarize               # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--U", type=float, default=0.10, help="ON duration (=W)")
    ap.add_argument("--G", type=float, default=0.90, help="mean OFF gap")
    ap.add_argument("--Ts", type=float, default=0.005)
    ap.add_argument("--cycles", type=int, default=200000)
    ap.add_argument("--arrivals", type=int, default=200000)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.cycles, args.arrivals, args.seeds = 20000, 20000, 4

    os.makedirs(RESULTS, exist_ok=True)
    U, G, Ts = args.U, args.G, args.Ts

    # ---------------- E13: residual law across segment types -------------
    print("=== E13 renewal residual law (mean R, atom) ===")
    segs = [("LEO det", "det", None), ("UAV jitter cv=0.3", "gamma", 0.3),
            ("CTMC exp cv=1", "exp", None), ("terr pareto cv=1.5", "pareto", 1.5)]
    e13_rows = []
    e13_ok = True
    for label, kind, cv in segs:
        samp = RN.gap_sampler(kind, G, cv)
        mr, mrcf, at, atcf = [], [], [], []
        for s in range(args.seeds):
            r = RN.residual_law(samp, U, args.cycles, args.arrivals, seed=12000 + s)
            mr.append(r.mean_R); mrcf.append(r.mean_R_cf)
            at.append(r.atom_frac); atcf.append(r.atom_cf)
        emr, emrcf = summarize(mr), summarize(mrcf)
        eat, eatcf = summarize(at), summarize(atcf)
        ok = emr.rel_error(emrcf.mean) < 0.04 and abs(eat.mean - eatcf.mean) < 0.01
        e13_ok = e13_ok and ok
        print(f"  {label:20}  E[R]={emr.mean:.4f} vs E[V^2]/2E[C]={emrcf.mean:.4f}  "
              f"atom={eat.mean:.4f} vs U/E[C]={eatcf.mean:.4f}  {'OK' if ok else 'FAIL'}")
        e13_rows.append(dict(segment=label, mean_R=emr.mean, mean_R_cf=emrcf.mean,
                             atom=eat.mean, atom_cf=eatcf.mean, passed=ok))
    _write_csv(os.path.join(RESULTS, "e13_renewal_residual.csv"), e13_rows)

    # ---------------- E12: AoI/PAoI inversion vs gap CV ------------------
    print("=== E12 AoI/PAoI inversion (sweep gap CV, fixed mean) ===")
    cvs = [0.0, 0.3, 0.5, 1.0, 1.5, 2.0]
    e12_rows = []
    e12_ok = True
    for cv in cvs:
        if cv == 0.0:
            samp = RN.gap_sampler("det", G)
        else:
            samp = RN.gap_sampler("gamma", G, cv)
        aois, paois, preds, obss = [], [], [], []
        for s in range(args.seeds):
            r = RN.aoi_paoi(samp, U, Ts, args.cycles, seed=13000 + s)
            aois.append(r.mean_aoi); paois.append(r.mean_paoi)
            preds.append(r.predicted_inversion); obss.append(r.observed_inversion)
        ea, ep = summarize(aois), summarize(paois)
        pred = sum(preds) / len(preds) > 0.5
        obs = sum(obss) / len(obss) > 0.5
        ok = (pred == obs)                      # theory predicts the sign correctly
        e12_ok = e12_ok and ok
        tag = "INVERTED" if obs else "normal"
        print(f"  CV={cv:3.1f}  AoI={ea.mean:.4f}  PAoI={ep.mean:.4f}  {tag:8} "
              f"(predict CV^2>1 -> {pred})  {'OK' if ok else 'FAIL'}")
        e12_rows.append(dict(cv=cv, mean_aoi=ea.mean, mean_paoi=ep.mean,
                             inverted=int(obs), predicted=int(pred), passed=ok))
    _write_csv(os.path.join(RESULTS, "e12_inversion.csv"), e12_rows)

    print(f"\nE13 {'PASS' if e13_ok else 'FAIL'} | E12 {'PASS' if e12_ok else 'FAIL'}")


def _write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  -> wrote {path}")


if __name__ == "__main__":
    main()
