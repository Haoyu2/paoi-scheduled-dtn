#!/usr/bin/env bash
# One full experiment run: generate plan, start ION, capture bpsink with recv
# timestamps, drive bpsource sender every 7.3 s, self-terminate, summarize.
# Usage: run_capture.sh <n_periods> <raw_log> <results_file>
set -u
N=${1:?n_periods}
RAWLOG=${2:?raw log path}
RESULTS=${3:?results path}

cd "$(dirname "$0")"
BASE=$PWD
export ION_NODE_LIST_DIR=$BASE
export PATH=/usr/local/bin:$PATH

RAWLOG="$BASE/$(basename "$RAWLOG")"
RESULTS="$BASE/$(basename "$RESULTS")"
SENTLOG="${RAWLOG%.log}_sent.log"
: > "$RAWLOG"; : > "$SENTLOG"

START=$(( $(date +%s) + 20 ))
python3 gen_plan.py "$START" "$N" > global.ionrc
echo "run_capture: start_epoch=$START n_periods=$N" | tee -a "$RAWLOG.meta"

./start_ion.sh

SEND_END=$(( START + 5 + (N-1)*60 + 6 - 1 ))
CAP_END=$(( START + 5 + (N-1)*60 + 6 + 15 ))

# Receiver: bpsink on ipn:2.1, prefix every output line with recv epoch.
cd "$BASE/node2"
stdbuf -oL bpsink ipn:2.1 > >(while IFS= read -r line; do
    printf '%s %s\n' "$(date +%s.%N)" "$line"
  done >> "$RAWLOG") 2>> "$BASE/bpsink.err" &
SINK_PID=$!
echo "bpsink pid $SINK_PID" >> "$RAWLOG.meta"
sleep 2

# Sender: every 7.3 s (incommensurate with P=60 s), payload = send epoch.
cd "$BASE/node1"
while [ "$(date +%s)" -lt "$SEND_END" ]; do
  ts=$(date +%s.%N)
  bpsource ipn:2.1 "$ts" >/dev/null 2>>"$BASE/bpsource.err"
  echo "$ts" >> "$SENTLOG"
  sleep 7.3
done

# Wait for the last window to flush all queued bundles.
now=$(date +%s)
[ "$now" -lt "$CAP_END" ] && sleep $(( CAP_END - now ))

kill "$SINK_PID" 2>/dev/null
sleep 2
cd "$BASE"
./stop_ion.sh >> "$RAWLOG.meta" 2>&1

python3 summarize.py "$RAWLOG" "$SENTLOG" "$START" > "$RESULTS"
echo "run_capture: done, results in $RESULTS" >> "$RAWLOG.meta"
