#!/bin/bash
# AoI-Energy policy comparison (K=4 relays). For each energy level (eta) and
# each strategy, record delivery, mean PAoI, and source energy (copies sent).
# Strategies: k1 (single CGR), k2/k3/k4 (Spray-and-Wait), epi (Epidemic).
# eta = harvestRate * GEN / e, GEN=300, e=1.
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
INI=policy_k4.ini
DEST=6
FAULT='--dtnsim.node[2..5].fault.enable=true --dtnsim.node[2..5].fault.meanTTF=8000s --dtnsim.node[2..5].fault.meanTTR=4000s'

deliv() { grep "node\[$DEST\].app appBundleReceived:count" "$1"|awk '{print $NF}'; }
srctx() { grep 'node\[1\].dtn dtnBundleSentToCom:count' "$1"|awk '{print $NF}'; }
paoi()  { python3 aoi_from_vec.py "$1" --dest $DEST --warmup-frac 0.1 --cluster-gap 600 2>/dev/null | awk '/mean PAoI/{print $4}'; }

run() {  # $1=tag, rest=routing args
  local tag=$1; shift
  local rd="pol_${tag}_${RATE}"; mkdir -p "$rd"
  $BIN -u Cmdenv -n "$NED" -f $INI "$@" \
    "--dtnsim.node[1].energy.harvestRate=$RATE" $FAULT --result-dir="$rd" >/dev/null 2>&1
  local sca="$rd/General-#0.sca" vec="$rd/General-#0.vec"
  printf '%s,%s,%s,%.0f,%s\n' "$ETA" "$tag" "$(deliv $sca)" "$(paoi $vec)" "$(srctx $sca)"
}

echo "eta,strategy,delivered,paoi,src_copies"
for RATE in 0.0017 0.0033 0.0050 0.0067 0.0100 0.0133 0.0200; do
  ETA=$(awk "BEGIN{printf \"%.2f\", $RATE*300}")
  run k1 '--dtnsim.node[*].dtn.routing="cgrModel350"'
  run k2 '--dtnsim.node[*].dtn.routing="sprayAndWait"' '--dtnsim.node[*].dtn.bundlesCopies=2'
  run k3 '--dtnsim.node[*].dtn.routing="sprayAndWait"' '--dtnsim.node[*].dtn.bundlesCopies=3'
  run k4 '--dtnsim.node[*].dtn.routing="sprayAndWait"' '--dtnsim.node[*].dtn.bundlesCopies=4'
  run epi '--dtnsim.node[*].dtn.routing="epidemic"'
done
