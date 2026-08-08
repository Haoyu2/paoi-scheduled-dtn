#!/usr/bin/env python3
"""Generate a Tier-2 dtnsim scenario for a periodic LEO segment.

Emits an ION-style contact plan and an OMNeT++ .ini matching the paper's
Result-1 LEO anchor (P=5736 s, W=430 s, delta~=0.075). Topology: a ground
source (node 1) reaches a gateway (node 2) only during periodic LEO
passes; bundles generated at node 1 must store-and-forward across the
scheduled gating, so end-to-end delay tracks the residual-wait law.

Stdlib-only. Writes:
    contactPlan/leo.txt   (m horizon / a contact lines)
    leo.ini               (OMNeT++ config; cgrModelRev17 routing)

    python3 sim/tier2/make_leo_scenario.py
"""
from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))

# --- scenario parameters (match sim/scenarios/leo_single.yaml) ---
P = 5736          # orbital period [s]  (~95.6 min, 550 km)
W = 430           # contact window [s]  (~7.2 min pass) -> delta ~= 0.075
N_PERIODS = 60    # horizon in periods
GEN_INTERVAL = 300   # bundle generation interval [s] (<< P to sample residual)
RATE = 1_000_000_000  # contact bitrate [bps]
BUNDLE_SIZE = 1024    # bytes
SRC, DST = 1, 2

HORIZON = P * N_PERIODS


def write_contact_plan(path):
    lines = [f"m horizon +{HORIZON}"]
    for n in range(N_PERIODS):
        s, e = n * P, n * P + W
        # bidirectional LEO pass between source and gateway
        lines.append(f"a contact +{s} +{e} {SRC} {DST} {RATE}")
        lines.append(f"a contact +{s} +{e} {DST} {SRC} {RATE}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return len(lines) - 1


def write_ini(path, cplan_rel):
    # generation epochs strictly inside the horizon
    starts = list(range(GEN_INTERVAL, HORIZON, GEN_INTERVAL))
    n = len(starts)
    start_str = ", ".join(str(t) for t in starts)
    ones = ", ".join(["1"] * n)
    dests = ", ".join([str(DST)] * n)
    sizes = ", ".join([str(BUNDLE_SIZE)] * n)
    ini = f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {HORIZON}s
dtnsim.nodesNumber = 2
dtnsim.node[*].dtn.sdrSize = 0            # 0 = infinite buffer
dtnsim.node[*].dtn.routing = "cgrModelRev17"
dtnsim.central.contactsFile = "{cplan_rel}"
dtnsim.node[*].dtn.routingType = "routeListType:allPaths-firstEnding,volumeAware:allContacts,extensionBlock:on,contactPlan:global"
dtnsim.node[*].dtn.printRoutingDebug = false
# record per-bundle delivery delay as a vector (time=delivery, value=latency Y)
# so AoI/PAoI can be reconstructed in post-processing
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all

# periodic status updates: node 1 -> node 2 (gateway)
dtnsim.node[{SRC}].app.enable = true
dtnsim.node[{SRC}].app.bundlesNumber = "{ones}"
dtnsim.node[{SRC}].app.start = "{start_str}"
dtnsim.node[{SRC}].app.destinationEid = "{dests}"
dtnsim.node[{SRC}].app.size = "{sizes}"
"""
    with open(path, "w") as f:
        f.write(ini)
    return n


def main():
    os.makedirs(os.path.join(HERE, "contactPlan"), exist_ok=True)
    cp = os.path.join(HERE, "contactPlan", "leo.txt")
    ini = os.path.join(HERE, "leo.ini")
    nc = write_contact_plan(cp)
    nb = write_ini(ini, "./contactPlan/leo.txt")
    print(f"horizon={HORIZON}s ({N_PERIODS} periods), delta={W/P:.4f}")
    print(f"wrote {cp}  ({nc} contacts)")
    print(f"wrote {ini}  ({nb} generation epochs)")


if __name__ == "__main__":
    main()
