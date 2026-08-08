#!/usr/bin/env python3
"""Per-run metric extraction for E17 (contact-capacity sensitivity).

Usage (from sim/tier2, after a dtnsim run):
    python3 e17_collect.py <result_dir>

Prints one CSV fragment (no k/gpp/m/seed prefix):
    generated,delivered,copies,delay_mean,opaoi

  generated  updates generated at the source (node[1].app appBundleSent)
  delivered  distinct updates delivered (dedup by generation time d - Y)
  copies     total copies delivered at the destination app
  delay_mean mean delivery delay over all delivered copies
  opaoi      per-outage OPAoI (cluster-gap 600 s), warmup 10% of horizon
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoi_from_vec import aoi_paoi, load_delay_vector  # noqa: E402

DEST = 5
WARMUP_FRAC = 0.1
CLUSTER_GAP = 600.0


def main():
    rd = sys.argv[1]
    vec = os.path.join(rd, "General-#0.vec")
    sca = os.path.join(rd, "General-#0.sca")

    pairs = load_delay_vector(vec, module_match=f"node[{DEST}].app")
    if pairs:
        horizon = max(d for d, _ in pairs)
        warm = WARMUP_FRAC * horizon
        _, opaoi, _ = aoi_paoi(pairs, warm, horizon, CLUSTER_GAP)
        delay = sum(y for _, y in pairs) / len(pairs)
        delivered = len({round(d - y, 3) for d, y in pairs})
        copies = len(pairs)
    else:
        opaoi = delay = float("nan")
        delivered = copies = 0

    generated = -1
    pat = re.compile(
        r"scalar dtnsim\.node\[1\]\.app appBundleSent:count (\S+)")
    with open(sca) as f:
        for line in f:
            m = pat.match(line)
            if m:
                generated = int(float(m.group(1)))

    print(f"{generated},{delivered},{copies},{delay:.2f},{opaoi:.1f}")


if __name__ == "__main__":
    main()
