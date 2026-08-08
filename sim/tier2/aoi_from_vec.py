#!/usr/bin/env python3
"""Reconstruct AoI/PAoI at the monitor from a dtnsim .vec result file.

dtnsim records appBundleReceivedDelay as a vector: each entry is
(delivery_time d, latency Y). The generation time is g = d - Y. We build
the monitor's age sawtooth (freshest delivered, LCFS) and report mean AoI
(time-average) and mean PAoI (per-period peak), to compare with the
PAoI = Z + Y composition (here the per-period contact gives Z = P).

    python3 sim/tier2/aoi_from_vec.py <results.vec> [--P 5736 --periods 60 --warmup 5]
"""
from __future__ import annotations

import argparse
import math


def load_delay_vector(path, module_match="node[2].app", name="appBundleReceivedDelay"):  # noqa: E501
    """Return list of (delivery_time, latency) from the matching vector."""
    vec_id = None
    cols = None
    out = []
    with open(path) as f:
        for line in f:
            if line.startswith("vector "):
                parts = line.split()
                # vector <id> <module> <name:vector> <columns>
                if module_match in parts[2] and parts[3].startswith(name):
                    vec_id = parts[1]
                    cols = parts[4] if len(parts) > 4 else "ETV"
                continue
            if vec_id is None:
                continue
            if line[:1].isdigit():
                p = line.split()
                if p[0] != vec_id:
                    continue
                # columns string e.g. "ETV": find positions of T and V
                ti = cols.index("T")
                vi = cols.index("V")
                # data layout: id then one field per column letter
                t = float(p[1 + ti])
                v = float(p[1 + vi])
                out.append((t, v))
    return out


def aoi_paoi(pairs, warmup, horizon, cluster_gap):
    """pairs = [(d, Y)]; build the monitor sawtooth.

    Returns (mean_aoi, mean_paoi, n). PAoI uses cluster-based peaks: resets
    within `cluster_gap` of each other belong to one contact burst and
    contribute a single peak (the max pre-reset age in the burst), so the
    many tiny in-window resets do not deflate PAoI. Works for regular and
    irregular (random-gap) contact plans alike.
    """
    evts = sorted((d, d - y) for d, y in pairs)   # (delivery, generation)
    monitor_g = -math.inf
    last_t = warmup
    area = 0.0
    peaks = []
    cluster_max = None
    last_reset = None
    for d, g in evts:
        if d <= warmup:
            if g > monitor_g:
                monitor_g = g
            continue
        if d > horizon:
            break
        if g <= monitor_g:
            continue                      # stale delivery: no reset
        if monitor_g > -math.inf:
            a0 = max(last_t, warmup) - monitor_g
            a1 = d - monitor_g            # age just before this reset
            area += 0.5 * (a0 + a1) * (d - max(last_t, warmup))
            if last_reset is None or d - last_reset > cluster_gap:
                if cluster_max is not None:
                    peaks.append(cluster_max)
                cluster_max = a1
            else:
                cluster_max = max(cluster_max, a1)
            last_reset = d
        monitor_g = g
        last_t = d
    if cluster_max is not None:
        peaks.append(cluster_max)
    span = horizon - warmup
    mean_aoi = area / span if span > 0 else float("nan")
    mean_paoi = sum(peaks) / len(peaks) if peaks else float("nan")
    return mean_aoi, mean_paoi, len(evts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vec")
    ap.add_argument("--dest", type=int, default=2, help="monitor node index")
    ap.add_argument("--warmup-frac", type=float, default=0.1,
                    help="fraction of horizon discarded as warmup")
    ap.add_argument("--cluster-gap", type=float, default=430,
                    help="resets within this gap = one contact burst (one peak)")
    args = ap.parse_args()

    pairs = load_delay_vector(args.vec, module_match=f"node[{args.dest}].app")
    if not pairs:
        print("no delay vector found (enable result-recording-modes=all and re-run)")
        return
    horizon = max(d for d, _ in pairs)
    warm = args.warmup_frac * horizon
    mean_aoi, mean_paoi, n = aoi_paoi(pairs, warm, horizon, args.cluster_gap)
    # standard per-reset PAoI (no clustering: every reset is its own peak)
    _, std_paoi, _ = aoi_paoi(pairs, warm, horizon, 0.0)
    ys = [y for _, y in pairs]
    my = sum(ys) / len(ys)
    sd = (sum((y - my) ** 2 for y in ys) / len(ys)) ** 0.5
    print(f"deliveries in vector: {n}")
    print(f"mean delivery delay (Y): {my:.2f}   std(Y): {sd:.2f}")
    print(f"mean AoI            : {mean_aoi:.1f} s")
    print(f"mean PAoI (per-outage): {mean_paoi:.1f} s   [primary, = E[Z]+E[Ymin]]")
    print(f"mean PAoI (per-reset) : {std_paoi:.1f} s   [textbook, counts every reset]")
    print(f"inversion (PAoI < AoI)? {mean_paoi < mean_aoi}")


if __name__ == "__main__":
    main()
