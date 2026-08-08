#!/usr/bin/env python3
"""Full heterogeneous end-to-end scenario for dtnsim (validates the title).

Chain: sensor(1) -> UAV mule(2) -> LEO(3) -> gateway(4), each hop a gated
store-carry-forward segment with its OWN contact model:
  seg1 1<->2  terrestrial opportunistic : heavy-tailed (gamma, CV>1) gaps
  seg2 2<->3  UAV semi-periodic         : periodic-with-jitter windows
  seg3 3<->4  LEO                        : deterministic periodic windows
Incommensurate cadences => phase mixing => end-to-end latency composes
additively, E[Y] = E[R1]+E[R2]+E[R3] (Sec 6.2). Finite battery optional at
the UAV/LEO relays.

    python3 make_hetero_scenario.py
"""
from __future__ import annotations

import argparse
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
RATE = 1_000_000_000
SIZE = 1024
GEN = 400
SEED = 7  # default; override with --seed
# seg1 terrestrial (heavy-tailed gaps)
G1, W1, CV1 = 3000.0, 300.0, 1.3
# seg2 UAV (periodic + jitter)
P2, W2, J2 = 1800.0, 180.0, 240.0
# seg3 LEO (deterministic periodic)
P3, W3 = 5736.0, 430.0
N3 = 60
HORIZON = int(P3 * N3)


def gamma_gap(rng, mean, cv):
    k = 1.0 / (cv * cv)
    return rng.gammavariate(k, mean * cv * cv)


def seg_terrestrial(rng):
    wins, t = [], 0.0
    while t < HORIZON:
        e = min(t + W1, HORIZON)
        if t < e:
            wins.append((t, e))
        t = e + gamma_gap(rng, G1, CV1)
    return wins


def seg_uav(rng):
    wins, last_end = [], 0.0
    n = 0
    while n * P2 < HORIZON:
        s = max(last_end, n * P2 + rng.gauss(0, J2))
        e = min(s + W2, HORIZON)
        if 0 <= s < e:
            wins.append((s, e)); last_end = e
        n += 1
    return wins


def seg_leo():
    wins, n = [], 0
    while n * P3 < HORIZON:
        s = n * P3
        e = min(s + W3, HORIZON)
        if s < e:
            wins.append((s, e))
        n += 1
    return wins


def residual_stats(wins):
    """E[R]=E[V^2]/2E[C], gaps V between consecutive windows, U=window len."""
    gaps = [wins[i + 1][0] - wins[i][1] for i in range(len(wins) - 1)]
    durs = [e - s for s, e in wins]
    EV = sum(gaps) / len(gaps)
    EV2 = sum(g * g for g in gaps) / len(gaps)
    EU = sum(durs) / len(durs)
    return EV2 / (2 * (EU + EV)), EV, EU


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    s1, s2, s3 = seg_terrestrial(rng), seg_uav(rng), seg_leo()
    lines = [f"m horizon +{HORIZON}"]
    for wins, a, b in ((s1, 1, 2), (s2, 2, 3), (s3, 3, 4)):
        for s, e in wins:
            lines.append(f"a contact +{int(s)} +{int(e)} {a} {b} {RATE}")
            lines.append(f"a contact +{int(s)} +{int(e)} {b} {a} {RATE}")
    os.makedirs(os.path.join(HERE, "contactPlan"), exist_ok=True)
    with open(os.path.join(HERE, "contactPlan", "hetero.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    starts = list(range(GEN, HORIZON, GEN))
    n = len(starts)
    with open(os.path.join(HERE, "hetero.ini"), "w") as f:
        f.write(f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {HORIZON}s
dtnsim.nodesNumber = 4
dtnsim.node[*].dtn.sdrSize = 0
dtnsim.node[*].dtn.routing = "cgrModel350"
dtnsim.central.contactsFile = "./contactPlan/hetero.txt"
dtnsim.node[*].dtn.printRoutingDebug = false
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all
# finite battery optional at the UAV(2) and LEO(3) relays (override per run)
dtnsim.node[2..3].energy.enable = false
dtnsim.node[2..3].energy.perCopyCost = 1
dtnsim.node[2..3].energy.batteryCapacity = 8
dtnsim.node[2..3].energy.batteryInit = 8
dtnsim.node[2..3].energy.harvestRate = 0.05
dtnsim.node[1].app.enable = true
dtnsim.node[1].app.bundlesNumber = "{', '.join(['1']*n)}"
dtnsim.node[1].app.start = "{', '.join(map(str, starts))}"
dtnsim.node[1].app.destinationEid = "{', '.join(['4']*n)}"
dtnsim.node[1].app.size = "{', '.join([str(SIZE)]*n)}"
""")
    r1, ev1, eu1 = residual_stats(s1)
    r2, ev2, eu2 = residual_stats(s2)
    r3, ev3, eu3 = residual_stats(s3)
    print(f"horizon={HORIZON}s, {n} updates; windows: terr={len(s1)} uav={len(s2)} leo={len(s3)}")
    print(f"  seg1 terrestrial: E[R1]={r1:.0f}s (E[V]={ev1:.0f}, CV-driven)")
    print(f"  seg2 UAV jitter : E[R2]={r2:.0f}s (E[V]={ev2:.0f})")
    print(f"  seg3 LEO        : E[R3]={r3:.0f}s (E[V]={ev3:.0f})")
    print(f"  predicted end-to-end mean delay E[Y]=E[R1]+E[R2]+E[R3] = {r1+r2+r3:.0f}s")


if __name__ == "__main__":
    main()
