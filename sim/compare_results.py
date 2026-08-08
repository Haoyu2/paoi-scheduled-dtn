#!/usr/bin/env python3
"""Compare reproduced result CSVs against the committed reference copies.

The committed paper dataset is frozen under <dir>/reference/ and is never
written by the experiment scripts; the scripts write <dir>/*.csv. After a
reproduction run:

    python3 compare_results.py                 # Tier-1: results/ vs results/reference/
    python3 compare_results.py tier2/results   # Tier-2
    python3 compare_results.py --rtol 0.05     # loosen tolerance (e.g. fewer seeds)

Numeric cells compare with relative tolerance (absolute below --atol);
non-numeric cells compare exactly. Exit code 0 iff every reference file is
matched within tolerance. Identical seeds and script defaults reproduce
Tier-1 bit-for-bit (Python's RNG is platform-independent); Tier-2 reruns
match to seed noise only if the same dtnsim commit and seeds are used.
"""
import argparse
import csv
import os
import sys


def is_num(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


def compare_file(ref_path, new_path, rtol, atol):
    with open(ref_path, newline="") as f:
        ref = list(csv.reader(f))
    with open(new_path, newline="") as f:
        new = list(csv.reader(f))
    if len(ref) != len(new):
        return False, f"row count {len(new)} vs reference {len(ref)}"
    worst = 0.0
    for i, (rrow, nrow) in enumerate(zip(ref, new)):
        if len(rrow) != len(nrow):
            return False, f"row {i}: column count {len(nrow)} vs {len(rrow)}"
        for j, (r, n) in enumerate(zip(rrow, nrow)):
            r, n = r.strip(), n.strip()
            if is_num(r) and is_num(n):
                rv, nv = float(r), float(n)
                if abs(rv - nv) <= atol:
                    continue
                dev = abs(rv - nv) / max(abs(rv), abs(nv), 1e-30)
                worst = max(worst, dev)
                if dev > rtol:
                    return False, (f"row {i} col {j}: {n} vs reference {r} "
                                   f"(rel dev {dev:.2e} > rtol {rtol:g})")
            elif r != n:
                return False, f"row {i} col {j}: {n!r} vs reference {r!r}"
    return True, f"max rel dev {worst:.2e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?", default="results",
                    help="working results dir (reference under <dir>/reference)")
    ap.add_argument("--rtol", type=float, default=1e-6,
                    help="relative tolerance for numeric cells")
    ap.add_argument("--atol", type=float, default=1e-12,
                    help="absolute tolerance floor")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    work = args.dir if os.path.isabs(args.dir) else os.path.join(here, args.dir)
    ref_dir = os.path.join(work, "reference")
    if not os.path.isdir(ref_dir):
        sys.exit(f"no reference dir at {ref_dir}")

    ok = missing = differ = 0
    for name in sorted(os.listdir(ref_dir)):
        if not name.endswith(".csv"):
            continue
        new_path = os.path.join(work, name)
        if not os.path.exists(new_path):
            print(f"MISSING  {name} (not reproduced yet)")
            missing += 1
            continue
        good, msg = compare_file(os.path.join(ref_dir, name), new_path,
                                 args.rtol, args.atol)
        if good:
            print(f"OK       {name} ({msg})")
            ok += 1
        else:
            print(f"DIFFERS  {name}: {msg}")
            differ += 1
    print(f"\n{ok} OK, {differ} differ, {missing} missing "
          f"(rtol {args.rtol:g})")
    sys.exit(1 if (differ or missing) else 0)


if __name__ == "__main__":
    main()
