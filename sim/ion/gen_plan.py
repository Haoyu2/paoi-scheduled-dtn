#!/usr/bin/env python3
"""Generate ION contact plan: window W=6s once per P=60s, first window at start+5.
Usage: gen_plan.py <start_epoch> <n_periods>  -> writes ionadmin commands to stdout."""
import sys, time

start = int(sys.argv[1])
N = int(sys.argv[2])

def ts(e):
    return time.strftime("%Y/%m/%d-%H:%M:%S", time.gmtime(e))

end = start + 5 + (N - 1) * 60 + 6 + 60
print("m horizon +0")
print(f"a range {ts(start)} {ts(end)} 1 2 1")
for n in range(N):
    a = start + 5 + 60 * n
    b = a + 6
    print(f"a contact {ts(a)} {ts(b)} 1 2 100000000")
    print(f"a contact {ts(a)} {ts(b)} 2 1 100000000")
