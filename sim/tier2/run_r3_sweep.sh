#!/bin/bash
# R3 energy sweep on wa: k=1 (single-copy CGR) vs k=2 (sprayAndWait, 2 copies)
# under random relay faults. Source has an energy gate; sweep harvestRate.
# eta = harvestRate * gen_interval / e  (gen=300, e=1).
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
FAULT='--dtnsim.node[2..3].fault.enable=true --dtnsim.node[2..3].fault.meanTTF=8000s --dtnsim.node[2..3].fault.meanTTR=4000s'

deliv() { grep 'node\[4\].app appBundleReceived:count' "$1"|awk '{print $NF}'; }
paoi() { python3 aoi_from_vec.py "$1" --dest 4 --warmup-frac 0.1 --cluster-gap 600 2>/dev/null | awk '/mean PAoI/{print $4}'; }

printf 'eta\tk1_deliv\tk1_paoi\tk2_deliv\tk2_paoi\n'
for rate in 0.0020 0.0033 0.0050 0.0067 0.0100 0.0200; do
  eta=$(awk "BEGIN{printf \"%.2f\", $rate*300}")
  rd1="sw_k1_$rate"; mkdir -p "$rd1"
  $BIN -u Cmdenv -n "$NED" -f r3_diamond.ini \
    '--dtnsim.node[*].dtn.routing="cgrModel350"' \
    "--dtnsim.node[1].energy.harvestRate=$rate" $FAULT \
    --result-dir="$rd1" >/dev/null 2>&1
  rd2="sw_k2_$rate"; mkdir -p "$rd2"
  $BIN -u Cmdenv -n "$NED" -f r3_diamond.ini \
    '--dtnsim.node[*].dtn.routing="sprayAndWait"' '--dtnsim.node[*].dtn.bundlesCopies=2' \
    "--dtnsim.node[1].energy.harvestRate=$rate" $FAULT \
    --result-dir="$rd2" >/dev/null 2>&1
  printf '%s\t%s\t%.0f\t%s\t%.0f\n' "$eta" \
    "$(deliv $rd1/General-#0.sca)" "$(paoi $rd1/General-#0.vec)" \
    "$(deliv $rd2/General-#0.sca)" "$(paoi $rd2/General-#0.vec)"
done
