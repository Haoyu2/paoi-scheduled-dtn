#!/usr/bin/env python3
"""Generate the R3 diamond scenario for dtnsim (energy + replication).

Topology: source(1) -> dest(4) via TWO independent bent-pipe relays
(2 and 3) with incommensurate pass periods. During relay i's pass both
1<->i and i<->4 are up, so a copy routed via relay i is delivered within
that pass; two independent relays give two independent delivery
opportunities (order-statistic Y_min for k=2).

Energy gate on the SOURCE only: each forwarded copy costs e, battery
harvests at lambda_e. k=2 (cgrModel350_2Copies) sends a copy to each
relay (2e/update); k=1 (cgrModel350) sends one (e/update). Sweeping
lambda_e crosses the R3 threshold eta = lambda_e * gen_interval / e.

Faults (optional) make a single route unreliable so replication actually
helps; without them, CGR on a deterministic plan already picks the best
route.

    python3 make_r3_scenario.py        # writes contactPlan + base ini
"""
from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
Pa, Wa = 5736, 430        # relay A pass period / window
Pb, Wb = 4500, 338        # relay B (incommensurate)
N_A = 60
RATE = 1_000_000_000
SIZE = 1024
GEN = 300
HORIZON = Pa * N_A


def passes(lines, period, width, a, b, c):
    """Bent-pipe relay `a` passes: during each window a<->b and a<->c up."""
    n = 0
    while n * period < HORIZON:
        s = n * period
        e = min(s + width, HORIZON)
        if s < e:
            for x, y in ((a, b), (b, a), (a, c), (c, a)):
                lines.append(f"a contact +{s} +{e} {x} {y} {RATE}")
        n += 1


def main():
    lines = [f"m horizon +{HORIZON}"]
    passes(lines, Pa, Wa, 2, 1, 4)    # relay A (node 2) bridges 1 and 4
    passes(lines, Pb, Wb, 3, 1, 4)    # relay B (node 3) bridges 1 and 4
    os.makedirs(os.path.join(HERE, "contactPlan"), exist_ok=True)
    cp = os.path.join(HERE, "contactPlan", "r3_diamond.txt")
    with open(cp, "w") as f:
        f.write("\n".join(lines) + "\n")

    starts = list(range(GEN, HORIZON, GEN))
    n = len(starts)
    ini = os.path.join(HERE, "r3_diamond.ini")
    with open(ini, "w") as f:
        f.write(f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {HORIZON}s
dtnsim.nodesNumber = 4
dtnsim.node[*].dtn.sdrSize = 0
dtnsim.node[*].dtn.routing = "cgrModel350"   # override per run (cgrModel350_2Copies for k=2)
dtnsim.central.contactsFile = "./contactPlan/r3_diamond.txt"
dtnsim.node[*].dtn.printRoutingDebug = false
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all

# energy gate on the source (node 1); relays/dest unlimited
dtnsim.node[1].energy.enable = true
dtnsim.node[1].energy.perCopyCost = 1
dtnsim.node[1].energy.batteryCapacity = 5
dtnsim.node[1].energy.batteryInit = 5
dtnsim.node[1].energy.harvestRate = 0.02     # override per run; eta = rate*{GEN}/e

# faults (optional): set meanTTF/meanTTR>0 to make single routes unreliable
dtnsim.node[*].fault.enable = false

dtnsim.node[1].app.enable = true
dtnsim.node[1].app.bundlesNumber = "{', '.join(['1']*n)}"
dtnsim.node[1].app.start = "{', '.join(map(str, starts))}"
dtnsim.node[1].app.destinationEid = "{', '.join(['4']*n)}"
dtnsim.node[1].app.size = "{', '.join([str(SIZE)]*n)}"
""")
    print(f"horizon={HORIZON}s, {n} updates; eta = harvestRate*{GEN}/e")
    print(f"wrote {cp}\nwrote {ini}")


if __name__ == "__main__":
    main()
