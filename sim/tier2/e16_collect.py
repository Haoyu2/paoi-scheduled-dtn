#!/usr/bin/env python3
"""Per-run metric extraction for E16 (unified fault+energy sweep).

Usage (from sim/tier2, after a dtnsim run):
    python3 e16_collect.py <result_dir>

Prints one CSV fragment (no eta/k/seed prefix):
    opaoi,paoi_per,delay_mean,updates_delivered,copies_delivered,admitted,skipped

  opaoi      per-outage OPAoI: cluster-gap 600 s peaks (aoi_from_vec primary)
  paoi_per   per-reset PAoI: every reset its own peak (= per-update PAoI
             under paced generation)
  delay_mean mean delivery delay over all delivered copies (freshest-copy
             semantics are already inside the AoI metrics; delay is raw)
  updates    distinct updates delivered (dedup by generation time d - Y)
  copies     total copies delivered at the destination app
  admitted / skipped
             exact atomic-admission counters recorded by the Energy module
             (node[1] scalars energyAdmittedUpdates / energySkippedUpdates);
             energy spent = admitted * k by construction.
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
        _, paoi_per, _ = aoi_paoi(pairs, warm, horizon, 0.0)
        delay = sum(y for _, y in pairs) / len(pairs)
        updates = len({round(d - y, 3) for d, y in pairs})
        copies = len(pairs)
    else:
        opaoi = paoi_per = delay = float("nan")
        updates = copies = 0

    admitted = skipped = -1
    pat = re.compile(
        r"scalar dtnsim\.node\[1\]\.energy energy(Admitted|Skipped)Updates (\S+)")
    with open(sca) as f:
        for line in f:
            m = pat.match(line)
            if m:
                val = int(float(m.group(2)))
                if m.group(1) == "Admitted":
                    admitted = val
                else:
                    skipped = val

    print(f"{opaoi:.1f},{paoi_per:.1f},{delay:.2f},"
          f"{updates},{copies},{admitted},{skipped}")


if __name__ == "__main__":
    main()
