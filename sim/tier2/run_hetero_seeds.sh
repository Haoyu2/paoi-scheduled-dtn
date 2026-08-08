#!/bin/bash
# Multi-seed heterogeneous end-to-end scenario (C): removes the single-seed
# caveat. For each seed: regenerate the contact plan, run dtnsim (energy off),
# compare simulated mean end-to-end delay against the additive prediction
# E[Y]=E[R1]+E[R2]+E[R3], and record mean PAoI.
# Output: results/hetero_seeds.csv  (seed,predicted,measured,err_pct,paoi)
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
SEEDS=${1:-10}
mkdir -p results

echo "seed,predicted,measured,err_pct,paoi"
for SD in $(seq 1 "$SEEDS"); do
  PRED=$(python3 make_hetero_scenario.py --seed "$SD" | awk '/predicted end-to-end/{print $(NF-0)}' | tr -d 's')
  RD="hs_${SD}"; mkdir -p "$RD"
  $BIN -u Cmdenv -n "$NED" -f hetero.ini "--seed-0-mt=$SD" --result-dir="$RD" >/dev/null 2>&1
  OUT=$(python3 aoi_from_vec.py "$RD/General-#0.vec" --dest 4 --warmup-frac 0.1 --cluster-gap 600 2>/dev/null)
  MEAS=$(echo "$OUT" | awk '/mean delivery delay/{print $5}')
  PAOI=$(echo "$OUT" | awk '/mean PAoI \(per-outage\)/{print $4}')
  ERR=$(awk "BEGIN{if($PRED>0) printf \"%.2f\", 100*($MEAS-$PRED)/$PRED; else print \"nan\"}")
  echo "$SD,$PRED,$MEAS,$ERR,$PAOI"
done
