#!/usr/bin/env python3
"""A2 scenario (B): two-satellite replication order statistic on REAL orbits.

Takes TWO Iridium-NEXT satellites from different orbital planes (real TLEs),
propagates both over the Svalbard ground station, and checks the paper's
order-statistic claims on the realized pass schedules:

  1. marginal residual law per satellite:  E[R_i] = E[V_i^2]/2E[C_i]  (Sec 6.5)
  2. two-copy delivered residual = min(R_1, R_2), and the heterogeneous
     product form (eq:rminprod):
        E[R_min] = integral prod_i P(R_i > r) dr
     which requires the two arrival phases to be INDEPENDENT -- exactly the
     staggered-plane assumption of Result 3.
  3. the realized two-copy gain E[R_min]/E[R_1] vs the co-period prediction
     (2/3)(1-delta).

No dtnsim needed: this is a direct Monte-Carlo over the real pass schedule.

    python3 two_tle_rmin.py [--days 7] [--arrivals 200000]
"""
from __future__ import annotations

import argparse
import math
import os
import random

from skyfield.api import load, wgs84

HERE = os.path.dirname(os.path.abspath(__file__))
TLE_FILE = os.path.join(HERE, "iridium.tle")
GS_LAT, GS_LON = 78.23, 15.39
MIN_ELEV = 10.0


def passes_for(sat, gs, ts, t0, days):
    t1 = ts.tt_jd(t0.tt + days)
    times, events = sat.find_events(gs, t0, t1, altitude_degrees=MIN_ELEV)
    base = t0.utc_datetime()
    out, rise = [], None
    for t, ev in zip(times, events):
        if ev == 0:
            rise = t
        elif ev == 2 and rise is not None:
            s = (rise.utc_datetime() - base).total_seconds()
            e = (t.utc_datetime() - base).total_seconds()
            if e > s >= 0:
                out.append((s, e))
            rise = None
    return out


def raan_deg(sat):
    return math.degrees(sat.model.nodeo)


def residual(t, wins):
    """Residual wait at time t: 0 if inside a window, else time to next rise."""
    for s, e in wins:
        if s <= t < e:
            return 0.0
        if t < s:
            return s - t
    return None  # past the last window


def renewal_pred(wins):
    gaps = [wins[i + 1][0] - wins[i][1] for i in range(len(wins) - 1)]
    durs = [e - s for s, e in wins]
    EV = sum(gaps) / len(gaps)
    EV2 = sum(g * g for g in gaps) / len(gaps)
    EU = sum(durs) / len(durs)
    return EV2 / (2 * (EU + EV)), EU, EV


def pair_stats(pA, pB, arrivals, seed):
    """Monte-Carlo residual stats for a satellite pair over their schedules."""
    horizon = min(pA[-1][1], pB[-1][1])
    rng = random.Random(seed)
    RA, RB = [], []
    margin = 0.9 * horizon
    for _ in range(arrivals):
        t = rng.uniform(0.0, margin)
        a, b = residual(t, pA), residual(t, pB)
        if a is None or b is None:
            continue
        RA.append(a); RB.append(b)
    n = len(RA)
    mA = sum(RA) / n
    mB = sum(RB) / n
    m_min = sum(min(a, b) for a, b in zip(RA, RB)) / n
    # heterogeneous product form (eq:rminprod) from EMPIRICAL marginals
    rmax = max(max(RA), max(RB))
    step = rmax / 4000.0
    sRA = sorted(RA); sRB = sorted(RB)

    def surv(sv, r):
        lo, hi = 0, len(sv)
        while lo < hi:
            mid = (lo + hi) // 2
            if sv[mid] <= r:
                lo = mid + 1
            else:
                hi = mid
        return (len(sv) - lo) / len(sv)

    prod_int = sum(surv(sRA, i * step) * surv(sRB, i * step)
                   for i in range(4001)) * step
    vA = sum((a - mA) ** 2 for a in RA) / n
    vB = sum((b - mB) ** 2 for b in RB) / n
    cov = sum((a - mA) * (b - mB) for a, b in zip(RA, RB)) / n
    rho = cov / math.sqrt(vA * vB)
    return mA, mB, m_min, prod_int, rho


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--arrivals", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--scan", type=int, default=0,
                    help="scan N companion satellites for phase alignment")
    args = ap.parse_args()

    ts = load.timescale()
    sats = load.tle_file(TLE_FILE)
    satA = sats[0]
    rA = raan_deg(satA)
    t0 = satA.epoch
    gs = wgs84.latlon(GS_LAT, GS_LON)
    pA = passes_for(satA, gs, ts, t0, args.days)
    predA, EU_A, EV_A = renewal_pred(pA)
    delta = EU_A / (EU_A + EV_A)
    gain_cf = (2.0 / 3.0) * (1 - delta)
    print(f"satA={satA.name!r} RAAN={rA:.1f}, {len(pA)} passes/{args.days}d, "
          f"GS=({GS_LAT},{GS_LON}); co-period ideal gain 2/3(1-delta)={gain_cf:.3f}")

    if args.scan:
        # sweep companions: phase alignment across the real constellation
        print("\nsatB              RAAN   rho     gain=E[Rmin]/E[R_A]  prod-form err%")
        rows = []
        for satB in sats[1:1 + args.scan]:
            try:
                pB = passes_for(satB, gs, ts, t0, args.days)
                if len(pB) < 20:
                    continue
                mA, mB, m_min, prod, rho = pair_stats(pA, pB, args.arrivals, args.seed)
                err = 100 * abs(m_min - prod) / prod
                rows.append((satB.name, raan_deg(satB), rho, m_min / mA, err))
                print(f"{satB.name:16s} {raan_deg(satB):6.1f} {rho:+.3f}  "
                      f"{m_min/mA:.3f}                {err:5.1f}")
            except Exception:
                continue
        best = min(rows, key=lambda r: r[3])
        worst = max(rows, key=lambda r: r[3])
        near_ind = min(rows, key=lambda r: abs(r[2]))
        print(f"\nbest-staggered pair : {best[0]} gain={best[3]:.3f} (rho={best[2]:+.3f})")
        print(f"most phase-locked   : {worst[0]} gain={worst[3]:.3f} (rho={worst[2]:+.3f})")
        print(f"nearest-independent : {near_ind[0]} rho={near_ind[2]:+.3f} "
              f"gain={near_ind[3]:.3f} prod-form err={near_ind[4]:.1f}%")
        print(f"ideal co-period gain: {gain_cf:.3f}")
        return

    satB = min(sats[1:], key=lambda s: abs((abs(raan_deg(s) - rA) % 180) - 90))
    pB = passes_for(satB, gs, ts, t0, args.days)
    predB, _, _ = renewal_pred(pB)
    mA, mB, m_min, prod_int, rho = pair_stats(pA, pB, args.arrivals, args.seed)
    print(f"satB={satB.name!r} RAAN={raan_deg(satB):.1f}; passes A={len(pA)} B={len(pB)}")
    print(f"\nmarginals (renewal law, Sec 6.5):")
    print(f"  satA: E[R]={mA:.1f}s vs E[V^2]/2E[C]={predA:.1f}s "
          f"({100*abs(mA-predA)/predA:.2f}% err)")
    print(f"  satB: E[R]={mB:.1f}s vs E[V^2]/2E[C]={predB:.1f}s "
          f"({100*abs(mB-predB)/predB:.2f}% err)")
    print(f"\ntwo-copy order statistic (eq:rminprod):")
    print(f"  empirical E[R_min]         = {m_min:.1f}s")
    print(f"  product-form prediction    = {prod_int:.1f}s "
          f"({100*abs(m_min-prod_int)/prod_int:.2f}% err)")
    print(f"  residual correlation rho   = {rho:+.3f}")
    print(f"  two-copy gain E[Rmin]/E[R1]= {m_min/mA:.3f} (ideal {gain_cf:.3f})")


if __name__ == "__main__":
    main()
