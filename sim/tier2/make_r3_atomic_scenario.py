#!/usr/bin/env python3
"""Generate the R3 ATOMIC-admission scenario for dtnsim (3-relay diamond).

Topology: source(1) -> dest(5) via THREE independent bent-pipe relays
(2, 3, 4). All three relays have the SAME pass period P and identical
windows W, but staggered phases (offsets 0, P/3, 2P/3) -- the staggered
contact-plan model. During relay i's pass both 1<->i and i<->5 are up,
so a copy routed via relay i is delivered within that pass.

NO faults: this is a pure energy-threshold test of the all-or-nothing
admission rule (Result 3). Energy gate on the SOURCE only, in ATOMIC
mode: an update is launched with exactly k copies iff the battery holds
>= k units (charged in one shot), else the whole update is skipped.
eta = harvestRate * P / perCopyCost  (energy per contact period, in
copies). Updates every GEN seconds, GEN incommensurate with P and
slightly larger, so one update ~ one period and eta_per_update ~= eta.

Per-seed randomization: the generation grid's initial phase offset
off0 ~ U(0, P) (baked into the ini start times); the contact plan is
seed-independent and shared.

    python3 make_r3_atomic_scenario.py --seeds 5
"""
from __future__ import annotations

import argparse
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
P = 5736                  # relay pass period (same for all 3 relays)
W = 430                   # pass window
OFFSETS = (0, P // 3, 2 * P // 3)   # staggered phases: 0, 1912, 3824
RATE = 1_000_000_000
SIZE = 1024
GEN = 6090.5              # update interval; GEN/P = 1.0618.. (incommensurate)
N_UPDATES = 460           # >=400 after 10% warmup
HORIZON = 2_820_000       # covers off0 + N*GEN + one extra period


def passes(lines, offset, a, b, c):
    """Bent-pipe relay `a` passes: during each window a<->b and a<->c up."""
    n = 0
    while offset + n * P < HORIZON:
        s = offset + n * P
        e = min(s + W, HORIZON)
        if s < e:
            for x, y in ((a, b), (b, a), (a, c), (c, a)):
                lines.append(f"a contact +{s} +{e} {x} {y} {RATE}")
        n += 1


def write_ini(seed):
    rng = random.Random(1000 + seed)
    off0 = rng.uniform(0, P)
    starts = [round(off0 + i * GEN, 1) for i in range(N_UPDATES)]
    n = len(starts)
    ini = os.path.join(HERE, f"r3_atomic_s{seed}.ini")
    with open(ini, "w") as f:
        f.write(f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {HORIZON}s
dtnsim.nodesNumber = 5
dtnsim.node[*].dtn.sdrSize = 0
dtnsim.node[*].dtn.routing = "cgrModelKCopies"
dtnsim.node[*].dtn.bundlesCopies = 1             # override per run (k)
dtnsim.central.contactsFile = "./contactPlan/r3_atomic.txt"
dtnsim.node[*].dtn.printRoutingDebug = false
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all

# ATOMIC all-or-nothing energy admission on the source (node 1) only:
# update launched with k copies iff battery >= k, else whole update
# skipped; k units charged at admission; per-transmission energy hooks
# are no-ops in atomic mode (no double charge). Relays/dest unlimited.
dtnsim.node[1].energy.enable = true
dtnsim.node[1].energy.atomic = true
dtnsim.node[1].energy.perCopyCost = 1
dtnsim.node[1].energy.batteryCapacity = 6
dtnsim.node[1].energy.batteryInit = 3
dtnsim.node[1].energy.harvestRate = 0.000174     # override per run; eta = rate*{P}/e

# NO faults: pure energy-threshold test
dtnsim.node[*].fault.enable = false

dtnsim.node[1].app.enable = true
dtnsim.node[1].app.bundlesNumber = "{', '.join(['1'] * n)}"
dtnsim.node[1].app.start = "{', '.join(map(str, starts))}"
dtnsim.node[1].app.destinationEid = "{', '.join(['5'] * n)}"
dtnsim.node[1].app.size = "{', '.join([str(SIZE)] * n)}"
""")
    print(f"seed {seed}: off0={off0:.1f}s -> {ini}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    lines = [f"m horizon +{HORIZON}"]
    for relay, off in zip((2, 3, 4), OFFSETS):
        passes(lines, off, relay, 1, 5)
    os.makedirs(os.path.join(HERE, "contactPlan"), exist_ok=True)
    cp = os.path.join(HERE, "contactPlan", "r3_atomic.txt")
    with open(cp, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"P={P} W={W} offsets={OFFSETS} GEN={GEN} horizon={HORIZON}s "
          f"({len(lines) - 1} contact lines)")
    print(f"wrote {cp}")
    for s in range(1, args.seeds + 1):
        write_ini(s)


if __name__ == "__main__":
    main()
