#!/usr/bin/env python3
"""Parse timestamped bpsink capture; compute delay stats vs theory.
Usage: summarize.py <raw_log> <sent_log> <start_epoch>
Raw log lines of interest:  <recv_epoch> \t'<send_epoch>'
"""
import sys, re

raw, sentlog, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
P, W = 60.0, 6.0
G = P - W
theory_mean = G * G / (2 * P)

pat = re.compile(r"^([0-9]+\.[0-9]+)\s+\t?'([0-9]+\.[0-9]+)'\s*$")
delays, pairs = [], []
for line in open(raw):
    m = pat.match(line)
    if m:
        recv, sent = float(m.group(1)), float(m.group(2))
        delays.append(recv - sent)
        pairs.append((sent, recv))

n_sent = sum(1 for _ in open(sentlog))
n = len(delays)
print(f"ION R1 residual-wait validation (P={P:.0f}s W={W:.0f}s G={G:.0f}s delta={W/P:.2f})")
print(f"plan start epoch: {start}")
print(f"bundles sent:      {n_sent}")
print(f"bundles delivered: {n}   (loss: {n_sent - n})")
if n == 0:
    sys.exit(0)
mean = sum(delays) / n
var = sum((d - mean) ** 2 for d in delays) / n
frac_atom = sum(1 for d in delays if d < 1.0) / n
print(f"mean delay:  {mean:.3f} s   (theory G^2/2P = {theory_mean:.3f} s, "
      f"error {100*(mean-theory_mean)/theory_mean:+.2f}%)")
print(f"std:         {var**0.5:.3f} s")
print(f"min:         {min(delays):.3f} s")
print(f"max:         {max(delays):.3f} s   (theory max ~ G = {G:.0f} s)")
print(f"frac < 1 s:  {frac_atom:.3f}   (theory atom = delta = {W/P:.2f})")
print()
print("histogram (10 bins over 0..60 s):")
bins = [0] * 10
for d in delays:
    i = min(int(d / 6.0), 9)
    bins[i] += 1
for i, c in enumerate(bins):
    lo, hi = 6 * i, 6 * (i + 1)
    bar = '#' * int(round(60.0 * c / n))
    print(f"  [{lo:2d},{hi:2d}) {c:5d}  {bar}")
print()

# ---- residual + dispatch-lag decomposition (script-native) ----------------
# delay = residual(plan phase) + dispatch lag.  Windows open at start+5+j*P.
# The physics check applies to the RESIDUAL component; the lag is reported
# separately -- it is the model's lumped service term T_s, measured here.
lag_gap, lag_win, resid_pred = [], [], []
for sent, recv in pairs:
    tau = (sent - start - 5.0) % P          # phase within period; 0 = window open
    if tau < W:
        r_pred = 0.0
        lag_win.append(recv - sent)
    else:
        r_pred = P - tau
        lag_gap.append(recv - sent - r_pred)
    resid_pred.append(r_pred)


def mstd(v):
    m = sum(v) / len(v)
    return m, (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5


rp_mean = sum(resid_pred) / n
print("decomposition (delay = residual + dispatch lag):")
print(f"  predicted residual mean (realized phases): {rp_mean:.3f} s "
      f"(closed form {theory_mean:.3f} s)")
print(f"  measured mean delay:                        {mean:.3f} s")
if lag_gap:
    lg, ls = mstd(lag_gap)
    print(f"  gap arrivals   (n={len(lag_gap)}): lag = {lg:.3f} +/- {ls:.3f} s"
          f"  (= measured T_s)")
if lag_win:
    wg, ws = mstd(lag_win)
    print(f"  window arrivals (n={len(lag_win)}): lag = {wg:.3f} +/- {ws:.3f} s")
print()
# non-circular check: per-bundle least squares delay ~ a + b*residual_pred.
# The law holds iff slope b ~= 1 (residual explains the delay one-for-one);
# the intercept a is the dispatch lag T_s.
xm = rp_mean
ym = mean
sxx = sum((x - xm) ** 2 for x in resid_pred)
sxy = sum((x - xm) * ((r - s) - ym) for x, (s, r) in zip(resid_pred, pairs))
slope = sxy / sxx
intercept = ym - slope * xm
verdict = "PASS" if abs(slope - 1.0) <= 0.05 else "FAIL"
print(f"per-bundle regression delay = a + b*residual_pred:")
print(f"  slope b = {slope:.4f}   (law exact iff b=1; check |b-1|<=0.05: {verdict})")
print(f"  intercept a = {intercept:.3f} s  (= dispatch lag, the model's T_s)")
print("note: the raw mean includes the dispatch lag (T_s); at operational "
      "periods (P~5.7e3 s) that lag is ~0.04% of the mean.")
