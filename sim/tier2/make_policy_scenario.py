#!/usr/bin/env python3
"""Generate a K-relay diamond for the AoI-Energy policy comparison (Result 3).

source(1) -> dest(K+2) via K independent bent-pipe relays (2..K+1) with
incommensurate pass periods, so up to K decorrelated paths are available
(K_max = K). Random relay faults make replication useful (hedging);
an energy gate on the source makes over-replication costly. This lets us
compare a single replication degree k=1..K (Spray-and-Wait), Epidemic,
and an adaptive policy k=k*(eta) against the energy budget.

    python3 make_policy_scenario.py [K]
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# roughly incommensurate relay pass periods [s]
PERIODS = [5736, 4500, 5100, 4790, 5410, 4230, 5550, 4960]
W = 430
N_BASE = 60          # horizon in periods of the (longest) relay
GEN = 300
RATE = 1_000_000_000
SIZE = 1024


def main():
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    periods = PERIODS[:K]
    src, dst = 1, K + 2
    relays = list(range(2, K + 2))
    horizon = max(periods) * N_BASE

    lines = [f"m horizon +{horizon}"]
    for relay, P in zip(relays, periods):
        n = 0
        while n * P < horizon:
            s = n * P
            e = min(s + W, horizon)
            if s < e:
                for a, b in ((src, relay), (relay, src), (relay, dst), (dst, relay)):
                    lines.append(f"a contact +{s} +{e} {a} {b} {RATE}")
            n += 1
    os.makedirs(os.path.join(HERE, "contactPlan"), exist_ok=True)
    cp = os.path.join(HERE, "contactPlan", f"policy_k{K}.txt")
    with open(cp, "w") as f:
        f.write("\n".join(lines) + "\n")

    starts = list(range(GEN, horizon, GEN))
    n = len(starts)
    ini = os.path.join(HERE, f"policy_k{K}.ini")
    with open(ini, "w") as f:
        f.write(f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {horizon}s
dtnsim.nodesNumber = {K + 2}
dtnsim.node[*].dtn.sdrSize = 0
dtnsim.node[*].dtn.routing = "cgrModel350"   # override per run
dtnsim.central.contactsFile = "./contactPlan/policy_k{K}.txt"
dtnsim.node[*].dtn.printRoutingDebug = false
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all
# energy gate on the source; relays/dest unlimited
dtnsim.node[1].energy.enable = true
dtnsim.node[1].energy.perCopyCost = 1
dtnsim.node[1].energy.batteryCapacity = {K + 1}
dtnsim.node[1].energy.batteryInit = {K + 1}
dtnsim.node[1].energy.harvestRate = 0.02     # override per run
# relays unreliable (override per run)
dtnsim.node[2..{K + 1}].fault.enable = false
dtnsim.node[1].app.enable = true
dtnsim.node[1].app.bundlesNumber = "{', '.join(['1'] * n)}"
dtnsim.node[1].app.start = "{', '.join(map(str, starts))}"
dtnsim.node[1].app.destinationEid = "{', '.join([str(dst)] * n)}"
dtnsim.node[1].app.size = "{', '.join([str(SIZE)] * n)}"
""")
    print(f"K={K} relays {relays} -> dest {dst}; horizon={horizon}s, {n} updates")
    print(f"wrote {cp}\nwrote {ini}")


if __name__ == "__main__":
    main()
