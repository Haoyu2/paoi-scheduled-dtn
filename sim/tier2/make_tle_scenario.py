#!/usr/bin/env python3
"""Generate a dtnsim contact plan from REAL LEO orbital passes (A1 scenario).

Propagates a real satellite (Iridium-NEXT TLE from CelesTrak) over a
ground station with Skyfield, extracts the contact windows (elevation >=
min), and writes a dtnsim contact plan + ini. The passes are
semi-periodic with varying gaps, so the relevant theory is the §6.5
alternating-renewal residual law: mean delivery delay = E[V^2]/2E[C].

Needs skyfield + numpy (installed on the VM). Saves the TLE snapshot
(iridium.tle) on first run for reproducibility.

    python3 make_tle_scenario.py
"""
from __future__ import annotations

import os
import urllib.request

from skyfield.api import load, wgs84

HERE = os.path.dirname(os.path.abspath(__file__))
TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=tle"
TLE_FILE = os.path.join(HERE, "iridium.tle")
GS_LAT, GS_LON = 78.23, 15.39      # Svalbard ground station (many LEO passes)
MIN_ELEV = 10.0                    # degrees
DAYS = 7
GEN = 300                          # status-update interval [s]
RATE = 1_000_000_000
SIZE = 1024


def get_tles():
    if not os.path.exists(TLE_FILE):
        urllib.request.urlretrieve(TLE_URL, TLE_FILE)
    return load.tle_file(TLE_FILE)


def main():
    ts = load.timescale()
    sats = get_tles()
    sat = sats[0]                  # first Iridium-NEXT satellite
    gs = wgs84.latlon(GS_LAT, GS_LON)
    t0 = sat.epoch
    t1 = ts.tt_jd(t0.tt + DAYS)
    times, events = sat.find_events(gs, t0, t1, altitude_degrees=MIN_ELEV)

    # pair rise(0) -> set(2) into pass windows; offset seconds from t0
    base = t0.utc_datetime()
    passes = []
    rise = None
    for t, ev in zip(times, events):
        if ev == 0:
            rise = t
        elif ev == 2 and rise is not None:
            s = (rise.utc_datetime() - base).total_seconds()
            e = (t.utc_datetime() - base).total_seconds()
            if e > s >= 0:
                passes.append((s, e))
            rise = None
    if not passes:
        raise SystemExit("no passes found")
    horizon = int(passes[-1][1]) + 1

    lines = [f"m horizon +{horizon}"]
    for s, e in passes:
        for a, b in ((1, 2), (2, 1)):
            lines.append(f"a contact +{int(s)} +{int(e)} {a} {b} {RATE}")
    with open(os.path.join(HERE, "contactPlan", "tle_leo.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    starts = list(range(GEN, horizon, GEN))
    n = len(starts)
    with open(os.path.join(HERE, "tle_leo.ini"), "w") as f:
        f.write(f"""[General]
network = src.dtnsim
repeat = 1
sim-time-limit = {horizon}s
dtnsim.nodesNumber = 2
dtnsim.node[*].dtn.sdrSize = 0
dtnsim.node[*].dtn.routing = "cgrModel350"
dtnsim.central.contactsFile = "./contactPlan/tle_leo.txt"
dtnsim.node[*].dtn.printRoutingDebug = false
dtnsim.node[*].app.appBundleReceivedDelay.result-recording-modes = all
dtnsim.node[1].app.enable = true
dtnsim.node[1].app.bundlesNumber = "{', '.join(['1']*n)}"
dtnsim.node[1].app.start = "{', '.join(map(str, starts))}"
dtnsim.node[1].app.destinationEid = "{', '.join(['2']*n)}"
dtnsim.node[1].app.size = "{', '.join([str(SIZE)]*n)}"
""")

    # realized renewal moments (gaps between consecutive passes)
    durs = [e - s for s, e in passes]
    gaps = [passes[i + 1][0] - passes[i][1] for i in range(len(passes) - 1)]
    EV = sum(gaps) / len(gaps)
    EV2 = sum(g * g for g in gaps) / len(gaps)
    EU = sum(durs) / len(durs)
    EC = EU + EV
    cv = (EV2 - EV * EV) ** 0.5 / EV
    print(f"sat={sat.name!r}  GS=({GS_LAT},{GS_LON})  {DAYS}d  passes={len(passes)}")
    print(f"  mean pass {EU:.0f}s, mean gap E[V]={EV:.0f}s, CV(V)={cv:.2f}, "
          f"duty delta={EU/EC:.4f}")
    print(f"  predicted mean delay = E[V^2]/2E[C] = {EV2/(2*EC):.1f}s")
    print(f"  horizon={horizon}s, {n} updates")


if __name__ == "__main__":
    main()
