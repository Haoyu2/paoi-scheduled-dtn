#!/bin/bash
# R3 two-sided comparison in real CGR: single-copy CGR vs CGR-native k=2
# (RoutingCgrModelKCopies) on the 2-relay diamond with faults + source energy
# gate. Multi-seed; emits raw per-seed rows: eta,strategy,seed,paoi,recv.
# PAoI from aoi_from_vec uses the freshest-arriving copy (order statistic).
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
DEST=4
SEEDS=10
paoi() { python3 aoi_from_vec.py "$1" --dest $DEST --warmup-frac 0.1 --cluster-gap 600 2>/dev/null | awk '/mean PAoI/{print $4}'; }
recv() { grep "node\[$DEST\].app appBundleReceived:count" "$1"|awk '{print $NF}'; }

run() {  # $1=tag rest=routing args ; uses $RATE $SD
  local tag=$1; shift
  local rd="cg_${tag}_${RATE}_${SD}"; mkdir -p "$rd"
  $BIN -u Cmdenv -n "$NED" -f r3_diamond.ini "$@" \
    "--dtnsim.node[1].energy.harvestRate=$RATE" \
    '--dtnsim.node[2..3].fault.enable=true' '--dtnsim.node[2..3].fault.meanTTF=8000s' \
    '--dtnsim.node[2..3].fault.meanTTR=4000s' \
    "--dtnsim.node[2..3].fault.faultSeed=$SD" "--seed-0-mt=$SD" \
    --result-dir="$rd" >/dev/null 2>&1
  printf '%s,%s,%s,%.0f,%s\n' "$ETA" "$tag" "$SD" "$(paoi $rd/General-#0.vec)" "$(recv $rd/General-#0.sca)"
}

echo "eta,strategy,seed,paoi,recv"
for RATE in 0.0020 0.0033 0.0050 0.0067 0.0100 0.0200; do
  ETA=$(awk "BEGIN{printf \"%.2f\", $RATE*300}")
  for SD in $(seq 1 $SEEDS); do
    run k1 '--dtnsim.node[*].dtn.routing="cgrModel350"'
    run cgr2 '--dtnsim.node[*].dtn.routing="cgrModelKCopies"' '--dtnsim.node[*].dtn.bundlesCopies=2'
  done
done
