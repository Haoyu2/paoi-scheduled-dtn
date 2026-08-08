#!/bin/bash
# Multi-seed R3 sweep (2-relay diamond, k=1 vs k=2) for confidence intervals.
# Varies the OMNeT++ RNG seed and the fault seed; emits raw per-seed rows.
# Output CSV columns: eta,strategy,seed,deliv,paoi
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
SEEDS=12
deliv() { grep "node\[$DEST\].app appBundleReceived:count" "$1"|awk '{print $NF}'; }
paoi()  { python3 aoi_from_vec.py "$1" --dest $DEST --warmup-frac 0.1 --cluster-gap 600 2>/dev/null | awk '/mean PAoI/{print $4}'; }

run() {  # $1=tag rest=routing args ; uses $RATE $SD
  local tag=$1; shift
  local rd="sd_${tag}_${RATE}_${SD}"; mkdir -p "$rd"
  $BIN -u Cmdenv -n "$NED" -f r3_diamond.ini "$@" \
    "--dtnsim.node[1].energy.harvestRate=$RATE" \
    '--dtnsim.node[2..3].fault.enable=true' '--dtnsim.node[2..3].fault.meanTTF=8000s' \
    '--dtnsim.node[2..3].fault.meanTTR=4000s' \
    "--dtnsim.node[2..3].fault.faultSeed=$SD" "--seed-0-mt=$SD" \
    --result-dir="$rd" >/dev/null 2>&1
  printf '%s,%s,%s,%s,%.0f\n' "$ETA" "$tag" "$SD" "$(deliv $rd/General-#0.sca)" "$(paoi $rd/General-#0.vec)"
}

echo "eta,strategy,seed,deliv,paoi"
for RATE in 0.0020 0.0033 0.0050 0.0067 0.0100 0.0200; do
  ETA=$(awk "BEGIN{printf \"%.2f\", $RATE*300}")
  for SD in $(seq 1 $SEEDS); do
    run k1 '--dtnsim.node[*].dtn.routing="cgrModel350"'
    run k2 '--dtnsim.node[*].dtn.routing="sprayAndWait"' '--dtnsim.node[*].dtn.bundlesCopies=2'
  done
done
