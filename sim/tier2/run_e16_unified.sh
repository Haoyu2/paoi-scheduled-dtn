#!/bin/bash
# E16 "unified" sweep: ONE topology (3-relay staggered diamond, the
# r3_atomic scenario as-is), ONE admission rule (atomic all-or-nothing at
# the source), RELAY FAULTS ON at nodes 2,3,4 (exponential meanTTF=8000s /
# meanTTR=4000s => availability ~2/3), BOTH peak metrics per run.
# Energy starvation (low eta, large k) and fault hedging (k>1 rides out a
# down relay) now compete in the SAME experiment.
#
# Sweep: k in {1,2,3} x eta in {1,2,3,6} x seeds. eta = harvestRate*P/e,
# P=5736, e=1. Faults draw from the global RNG (seed-0-mt), so the fault
# sample path is common across (k,eta) at a given seed (paired runs);
# fault.faultSeed is set for bookkeeping only (unused by Fault.cc).
#
# Emits raw per-run rows to results/e16_unified_raw.csv:
#   eta,k,seed,opaoi,paoi_per,delay_mean,updates_delivered,copies_delivered,admitted,skipped
# then aggregates to results/e16_unified.csv via e16_aggregate.py.
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
P=5736
SEEDS="${SEEDS:-1 2 3 4 5 6 7 8 9 10}"
ETAS="${ETAS:-1.0 2.0 3.0 6.0}"
KS="${KS:-1 2 3}"
TTF="${TTF:-8000}"
TTR="${TTR:-4000}"
OUT=results/e16_unified_raw.csv

# APPEND=1 adds rows to an existing raw csv (e.g. extra seeds); default fresh
if [ "${APPEND:-0}" != 1 ]; then
  echo "eta,k,seed,opaoi,paoi_per,delay_mean,updates_delivered,copies_delivered,admitted,skipped" > "$OUT"
fi
for ETA in $ETAS; do
  RATE=$(awk "BEGIN{printf \"%.9f\", $ETA/$P}")
  for K in $KS; do
    for SD in $SEEDS; do
      rd="e16_${K}_${ETA}_${SD}"; mkdir -p "$rd"
      $BIN -u Cmdenv -n "$NED" -f "r3_atomic_s${SD}.ini" \
        "--dtnsim.node[*].dtn.bundlesCopies=$K" \
        "--dtnsim.node[1].energy.harvestRate=$RATE" \
        '--dtnsim.node[2..4].fault.enable=true' \
        "--dtnsim.node[2..4].fault.meanTTF=${TTF}s" \
        "--dtnsim.node[2..4].fault.meanTTR=${TTR}s" \
        "--dtnsim.node[2..4].fault.faultSeed=$SD" \
        "--seed-0-mt=$SD" \
        --result-dir="$rd" >/dev/null 2>&1
      row=$(python3 e16_collect.py "$rd")
      echo "$ETA,$K,$SD,$row" | tee -a "$OUT"
    done
  done
done
echo "raw done -> $OUT"
python3 e16_aggregate.py
