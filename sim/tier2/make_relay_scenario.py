#!/usr/bin/env python3
"""Generate a 2-segment relay scenario (sensor -> sat -> gateway) for dtnsim.

Tests the Result-2 phase-mixing lemma in real CGR. Node 1 (sensor) reaches
node 3 (gateway) only via node 2 (LEO relay): contacts 1<->2 (segment 1)
and 2<->3 (segment 2) are scheduled at different times, so a bundle
store-carry-forwards across two gated hops. End-to-end latency
Y = R1 + R2 (+tx).

Two modes:
  incomm  -- incommensurate periods P1 != P2  => phases mix, R1 _|_ R2,
             so Var(Y) = Var(R1) + Var(R2)  (lemma holds).
  comm    -- commensurate P2 = P1 with the 2<->3 window offset by P/2 =>
             phases lock, R2 becomes ~constant, Var(Y) ~ Var(R1) only.

    python3 make_relay_scenario.py incomm
    python3 make_relay_scenario.py comm
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RATE = 1_000_000_000
SIZE = 1024
GEN_INTERVAL = 300
N1_PERIODS = 60          # horizon counted in segment-1 periods


def residual_moments(P, W):
    G = P - W
    ER = G * G / (2 * P)
    ER2 = G ** 3 / (3 * P)
    return ER, ER2 - ER * ER          # mean, variance


def build(mode):
    if mode == "incomm":
        P1, W1, off1 = 5736, 430, 0
        P2, W2, off2 = 4500, 338, 0
    elif mode == "comm":
        P1, W1, off1 = 5736, 430, 0
        P2, W2, off2 = 5736, 430, 2868     # P2 = P1, 2<->3 offset by P/2
    else:
        raise SystemExit("mode must be 'incomm' or 'comm'")
    horizon = P1 * N1_PERIODS

    # --- contact plan: seg1 = 1<->2 (period P1), seg2 = 2<->3 (period P2) ---
    lines = [f"m horizon +{horizon}"]

    def passes(period, width, off, a, b):
        n = 0
        while True:
            s = n * period + off
            if s >= horizon:
                break
            e = min(s + width, horizon)
            if s < e:
                lines.append(f"a contact +{s} +{e} {a} {b} {RATE}")
                lines.append(f"a contact +{s} +{e} {b} {a} {RATE}")
            n += 1
    passes(P1, W1, off1, 1, 2)
    passes(P2, W2, off2, 2, 3)
    cp = os.path.join(HERE, "contactPlan", f"relay_{mode}.txt")
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    with open(cp, "w") as f:
        f.write("\n".join(lines) + "\n")

    # --- traffic: node 1 -> node 3 every GEN_INTERVAL ---
    starts = list(range(GEN_INTERVAL, horizon, GEN_INTERVAL))
    n = len(starts)
    ini = os.path.join(HERE, f"relay_{mode}.ini")
    with open(ini, "w") as f:
        f.write(f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {horizon}s
dtnsim.nodesNumber = 3
dtnsim.node[*].dtn.sdrSize = 0
dtnsim.node[*].dtn.routing = "cgrModelRev17"
dtnsim.central.contactsFile = "./contactPlan/relay_{mode}.txt"
dtnsim.node[*].dtn.routingType = "routeListType:allPaths-firstEnding,volumeAware:allContacts,extensionBlock:on,contactPlan:global"
dtnsim.node[*].dtn.printRoutingDebug = false
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all
dtnsim.node[1].app.enable = true
dtnsim.node[1].app.bundlesNumber = "{', '.join(['1']*n)}"
dtnsim.node[1].app.start = "{', '.join(map(str, starts))}"
dtnsim.node[1].app.destinationEid = "{', '.join(['3']*n)}"
dtnsim.node[1].app.size = "{', '.join([str(SIZE)]*n)}"
""")

    er1, v1 = residual_moments(P1, W1)
    er2, v2 = residual_moments(P2, W2)
    print(f"mode={mode}: P1={P1},W1={W1}  P2={P2},W2={W2},off2={off2}  horizon={horizon}s")
    print(f"  predicted E[R1]={er1:.1f} E[R2]={er2:.1f} -> E[Y]={er1+er2:.1f}")
    if mode == "incomm":
        import math
        print(f"  predicted Var(Y)=Var(R1)+Var(R2)={v1+v2:.0f} -> sd(Y)={math.sqrt(v1+v2):.1f}")
    else:
        import math
        print(f"  locked: R2~=P/2 const -> E[Y]={er1 + off2:.1f}, "
              f"Var(Y)~=Var(R1)={v1:.0f} -> sd(Y)={math.sqrt(v1):.1f}")
    print(f"  wrote {cp}\n  wrote {ini}  ({n} updates)")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "incomm")
