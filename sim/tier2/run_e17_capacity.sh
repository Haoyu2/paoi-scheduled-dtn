#!/bin/bash
# E17 contact-capacity sensitivity: where the low-load assumption breaks.
# Window capacity m bundles is set via the contact-plan rate (BYTES/s in
# dtnsim: txDuration = bytes/rate; CGR 350 is volume-aware), rate =
# ceil(SIZE*m/W). Offered load gpp = updates per period (GEN = P/gpp).
#   k=1 runs on the SINGLE-relay plan  (per-window offered copies = gpp)
#   k=2 runs on the 3-relay DIAMOND    (per-window offered copies ~ 2*gpp/3,
#                                       per-relay window capacity still m)
# m=64 is the uncongested reference; m=8 makes the sweep cross capacity.
# No energy gating, no faults. 3 seeds (generation-grid phase off0~U(0,P)).
#
# Emits raw rows to results/e17_capacity_raw.csv:
#   k,gen_per_period,window_capacity_m,seed,generated,delivered,copies,delay_mean,opaoi
# then aggregates to results/e17_capacity.csv via e17_aggregate.py.
set -eo pipefail  # fail fast; -u is enabled only after setenv (it reads unset vars)
OMNETPP_HOME="${OMNETPP_HOME:-$HOME/omnetpp-5.7.1}"
DTNSIM_ROOT="${DTNSIM_ROOT:-$HOME/dtnsim/dtnsim}"
source "$OMNETPP_HOME/setenv" -f >/dev/null 2>&1 \
  || { echo "error: cannot source $OMNETPP_HOME/setenv (set OMNETPP_HOME)" >&2; exit 1; }
set -u
cd "$(dirname "$0")" || exit 1
BIN="$DTNSIM_ROOT/dtnsim"
NED="$DTNSIM_ROOT/src:$DTNSIM_ROOT"
[ -x "$BIN" ] || { echo "error: dtnsim binary not found at $BIN (set DTNSIM_ROOT)" >&2; exit 1; }
SEEDS="${SEEDS:-1 2 3}"
MS="${MS:-64 8}"
KS="${KS:-1 2}"
GPPS="${GPPS:-1.05 2 4 8 16}"
OUT=results/e17_capacity_raw.csv

echo "k,gen_per_period,window_capacity_m,seed,generated,delivered,copies,delay_mean,opaoi" > "$OUT"
for M in $MS; do
  for K in $KS; do
    if [ "$K" = 1 ]; then TOPO=single; else TOPO=diamond; fi
    CP="./contactPlan/e17_${TOPO}_m${M}.txt"
    for GPP in $GPPS; do
      for SD in $SEEDS; do
        rd="e17_${K}_${M}_${GPP}_${SD}"; mkdir -p "$rd"
        $BIN -u Cmdenv -n "$NED" -f "e17_g${GPP}_s${SD}.ini" \
          "--dtnsim.central.contactsFile=\"$CP\"" \
          "--dtnsim.node[*].dtn.bundlesCopies=$K" \
          "--seed-0-mt=$SD" \
          --result-dir="$rd" >/dev/null 2>&1
        row=$(python3 e17_collect.py "$rd")
        echo "$K,$GPP,$M,$SD,$row" | tee -a "$OUT"
      done
    done
  done
done
echo "raw done -> $OUT"
python3 e17_aggregate.py
