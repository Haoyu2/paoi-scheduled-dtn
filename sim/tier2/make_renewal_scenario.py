#!/usr/bin/env python3
"""Generate a single-segment dtnsim scenario with RANDOM contact gaps (sec 6.5).

A node-1 -> node-2 link whose contact windows (width W) are separated by
OFF gaps V drawn from a distribution with mean G. Tests the alternating-
renewal residual law in real CGR:
    mean delivery delay  ->  E[V^2]/(2 E[C])
and the AoI/PAoI inversion: mean PAoI ~ E[V] (cadence) while mean AoI ~
E[V^2]/(2 E[C]) grows with gap variance -> PAoI < AoI when CV(V) > 1.

    python3 make_renewal_scenario.py gamma 0.5     # UAV jitter (CV<1)
    python3 make_renewal_scenario.py exp           # CTMC (CV=1)
    python3 make_renewal_scenario.py pareto 1.5    # terrestrial heavy tail (CV>1)
"""
from __future__ import annotations

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = 430            # contact window width [s]
G = 5306           # mean OFF gap [s]  (E[C]=W+G=5736, delta~=0.075)
N_WINDOWS = 300
GEN_INTERVAL = 400
RATE = 1_000_000_000
SIZE = 1024
SEED = 12345


def sampler(kind, cv):
    if kind == "exp":
        return lambda r: r.expovariate(1.0 / G)
    if kind == "gamma":
        k, theta = 1.0 / (cv * cv), G * cv * cv
        return lambda r: r.gammavariate(k, theta)
    if kind == "pareto":
        a = 1.0 + math.sqrt(1.0 + 1.0 / (cv * cv))
        xm = G * (a - 1.0) / a
        return lambda r: xm / (r.random() ** (1.0 / a))
    raise SystemExit("kind in {gamma,exp,pareto}")


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "exp"
    cv = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    tag = f"{kind}{str(cv).replace('.', '')}" if kind != "exp" else "exp"
    samp = sampler(kind, cv)
    rng = random.Random(SEED)

    gaps = [samp(rng) for _ in range(N_WINDOWS)]
    # build windows separated by the sampled gaps
    lines = []
    t = 0.0
    for V in gaps:
        s, e = t, t + W
        lines.append(f"a contact +{int(s)} +{int(e)} 1 2 {RATE}")
        lines.append(f"a contact +{int(s)} +{int(e)} 2 1 {RATE}")
        t = e + V
    horizon = int(t)
    lines.insert(0, f"m horizon +{horizon}")
    cp = os.path.join(HERE, "contactPlan", f"renewal_{tag}.txt")
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    with open(cp, "w") as f:
        f.write("\n".join(lines) + "\n")

    starts = list(range(GEN_INTERVAL, horizon, GEN_INTERVAL))
    n = len(starts)
    ini = os.path.join(HERE, f"renewal_{tag}.ini")
    with open(ini, "w") as f:
        f.write(f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {horizon}s
dtnsim.nodesNumber = 2
dtnsim.node[*].dtn.sdrSize = 0
dtnsim.node[*].dtn.routing = "cgrModelRev17"
dtnsim.central.contactsFile = "./contactPlan/renewal_{tag}.txt"
dtnsim.node[*].dtn.routingType = "routeListType:allPaths-firstEnding,volumeAware:allContacts,extensionBlock:on,contactPlan:global"
dtnsim.node[*].dtn.printRoutingDebug = false
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all
dtnsim.node[1].app.enable = true
dtnsim.node[1].app.bundlesNumber = "{', '.join(['1']*n)}"
dtnsim.node[1].app.start = "{', '.join(map(str, starts))}"
dtnsim.node[1].app.destinationEid = "{', '.join(['2']*n)}"
dtnsim.node[1].app.size = "{', '.join([str(SIZE)]*n)}"
""")

    EV = sum(gaps) / len(gaps)
    EV2 = sum(v * v for v in gaps) / len(gaps)
    EC = W + EV
    cv_real = math.sqrt(EV2 - EV * EV) / EV
    print(f"kind={kind} cv={cv}  realized: E[V]={EV:.1f} CV(V)={cv_real:.2f} "
          f"E[C]={EC:.1f}  horizon={horizon}s, {n} updates")
    print(f"  predicted mean delay Y = E[V^2]/2E[C] = {EV2/(2*EC):.1f}")
    print(f"  predicted mean PAoI ~ E[V] = {EV:.1f}; "
          f"inversion (PAoI<AoI)? CV^2>1 -> {cv_real**2 > 1}")
    print(f"  wrote {cp}\n  wrote {ini}")


if __name__ == "__main__":
    main()
