#!/bin/bash
# R3 ATOMIC all-or-nothing admission sweep: k in {1,2,3} x eta x seeds on
# the 3-relay staggered diamond (no faults). eta = harvestRate * P / e,
# P=5736, e=1. Emits raw per-run rows to results/r3_atomic_raw.csv:
#   eta,k,seed,paoi,updates_delivered,copies_delivered
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
DEST=5
P=5736
SEEDS="${SEEDS:-1 2 3 4 5}"
ETAS="${ETAS:-0.6 1.0 1.5 2.0 3.0 6.0}"
KS="${KS:-1 2 3}"
OUT=results/r3_atomic_raw.csv

paoi() { python3 aoi_from_vec.py "$1" --dest $DEST --warmup-frac 0.1 --cluster-gap 600 2>/dev/null | awk '/per-outage/{print $4}'; }
# distinct updates delivered (unique generation times) + total copies
updates() {
python3 - "$1" <<'EOF'
import sys
sys.path.insert(0, ".")
from aoi_from_vec import load_delay_vector
pairs = load_delay_vector(sys.argv[1], module_match="node[5].app")
gens = {round(d - y, 3) for d, y in pairs}
print(f"{len(gens)},{len(pairs)}")
EOF
}

echo "eta,k,seed,paoi,updates_delivered,copies_delivered" > "$OUT"
for ETA in $ETAS; do
  RATE=$(awk "BEGIN{printf \"%.9f\", $ETA/$P}")
  for K in $KS; do
    for SD in $SEEDS; do
      rd="at_${K}_${ETA}_${SD}"; mkdir -p "$rd"
      $BIN -u Cmdenv -n "$NED" -f "r3_atomic_s${SD}.ini" \
        "--dtnsim.node[*].dtn.bundlesCopies=$K" \
        "--dtnsim.node[1].energy.harvestRate=$RATE" \
        "--seed-0-mt=$SD" \
        --result-dir="$rd" >/dev/null 2>&1
      pv=$(paoi "$rd/General-#0.vec")
      uc=$(updates "$rd/General-#0.vec")
      echo "$ETA,$K,$SD,$pv,$uc" | tee -a "$OUT"
    done
  done
done
echo "raw done -> $OUT"
python3 r3_atomic_aggregate.py
