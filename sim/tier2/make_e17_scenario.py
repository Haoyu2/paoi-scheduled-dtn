#!/usr/bin/env python3
"""Generate the E17 contact-capacity sensitivity scenario for dtnsim.

Question: where does the paper's low-load assumption (a contact window
swallows whatever is queued) break? We cap the per-window capacity via
the contact-plan data rate and raise the offered update rate.

CAPACITY MAPPING (dtnsim mechanics, verified in src/node/dtn/Dtn.cc and
routing/RoutingCgrModel350.cc):
  - contact-plan rate is in BYTES/S: txDuration = byteLength / dataRate.
  - CGR 350 is volume-aware: a route whose first contact has residual
    volume < bundle size is skipped, so bookings spill to later windows.
  - both mechanisms give window capacity m = floor(rate * W / SIZE)
    bundles; we set rate = ceil(SIZE * m / W)  [BYTES/s, not bits].
    m=64 -> rate=153 B/s (floor(153*430/1024)=64 exactly)
    m=8  -> rate= 20 B/s (floor( 20*430/1024)= 8 exactly)
  - the bent pipe re-sends within the same window on the relay->dest
    contact (same rate), so effective end-to-end per-window throughput is
    ~m with a <=1-bundle pipeline edge (a copy landing in the last
    txDuration of the window rides the NEXT relay->dest window).

Topologies (P=5736, W=430, same bent-pipe geometry as r3_atomic):
  single : source 1 -> relay 2 (offset 0)            -> dest 5   [k=1 runs]
           offered copies per window = gpp (all updates share one window)
  diamond: source 1 -> relays 2,3,4 (offsets 0,P/3,2P/3) -> dest 5 [k=2]
           k=2 copies go to the 2 earliest distinct relay passes, so each
           window carries ~2*gpp/3 copies (per-relay capacity still m)

Offered load: GEN in {P/1.05, P/2, P/4, P/8, P/16} = gpp updates per
period in {1.05, 2, 4, 8, 16}. Per-seed randomization: generation-grid
phase off0 ~ U(0, P). No energy gating, no faults.

Writes contactPlan/e17_{single,diamond}_m{8,64}.txt and
e17_g{gpp}_s{seed}.ini (run script picks plan + k per run).

    python3 make_e17_scenario.py --seeds 3
"""
from __future__ import annotations

import argparse
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
P = 5736
W = 430
SIZE = 1024               # bundle size [bytes]
M_LIST = (64, 8)          # window capacity [bundles]: uncongested ref + knee
GPP_LIST = (1.05, 2, 4, 8, 16)   # offered updates per period (GEN = P/gpp)
HORIZON = 1_200_000       # ~209 periods
TAIL = 2 * P              # stop generating near the horizon (drain margin)
OFFSETS_DIAMOND = (0, P // 3, 2 * P // 3)


def rate_for(m):
    return math.ceil(SIZE * m / W)          # BYTES per second


def passes(lines, offset, relay, rate):
    n = 0
    while offset + n * P < HORIZON:
        s = offset + n * P
        e = min(s + W, HORIZON)
        if s < e:
            for x, y in ((relay, 1), (1, relay), (relay, 5), (5, relay)):
                lines.append(f"a contact +{s} +{e} {x} {y} {rate}")
        n += 1


def write_plan(name, relays_offsets, rate):
    lines = [f"m horizon +{HORIZON}"]
    for relay, off in relays_offsets:
        passes(lines, off, relay, rate)
    path = os.path.join(HERE, "contactPlan", name)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {path}  ({len(lines) - 1} contact lines, rate={rate} B/s)")


def gpp_tag(gpp):
    return f"{gpp:g}"


def write_ini(gpp, seed):
    gen = P / gpp
    rng = random.Random(7000 + 100 * int(gpp * 100) + seed)
    off0 = rng.uniform(0, P)
    starts = []
    t = off0
    while t <= HORIZON - TAIL:
        starts.append(round(t, 1))
        t += gen
    n = len(starts)
    ini = os.path.join(HERE, f"e17_g{gpp_tag(gpp)}_s{seed}.ini")
    with open(ini, "w") as f:
        f.write(f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {HORIZON}s
dtnsim.nodesNumber = 5
dtnsim.node[*].dtn.sdrSize = 0
dtnsim.node[*].dtn.routing = "cgrModelKCopies"
dtnsim.node[*].dtn.bundlesCopies = 1             # override per run (k)
dtnsim.central.contactsFile = "./contactPlan/e17_single_m64.txt"  # override per run
dtnsim.node[*].dtn.printRoutingDebug = false
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all

# E17: pure capacity test -- no energy gating, no faults
dtnsim.node[*].energy.enable = false
dtnsim.node[*].fault.enable = false

dtnsim.node[1].app.enable = true
dtnsim.node[1].app.bundlesNumber = "{', '.join(['1'] * n)}"
dtnsim.node[1].app.start = "{', '.join(map(str, starts))}"
dtnsim.node[1].app.destinationEid = "{', '.join(['5'] * n)}"
dtnsim.node[1].app.size = "{', '.join([str(SIZE)] * n)}"
""")
    print(f"gpp={gpp} seed={seed}: GEN={gen:.1f}s off0={off0:.1f}s "
          f"n={n} -> {ini}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()

    os.makedirs(os.path.join(HERE, "contactPlan"), exist_ok=True)
    for m in M_LIST:
        r = rate_for(m)
        eff = (r * W) // SIZE
        assert eff == m, f"m={m}: rate {r} gives capacity {eff}"
        write_plan(f"e17_single_m{m}.txt", [(2, 0)], r)
        write_plan(f"e17_diamond_m{m}.txt",
                   list(zip((2, 3, 4), OFFSETS_DIAMOND)), r)
    for gpp in GPP_LIST:
        for s in range(1, args.seeds + 1):
            write_ini(gpp, s)


if __name__ == "__main__":
    main()
