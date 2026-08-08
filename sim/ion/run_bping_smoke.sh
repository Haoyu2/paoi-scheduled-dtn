#!/usr/bin/env bash
set -euo pipefail

ION_SRC="${ION_SRC:-$HOME/src/ION-DTN}"

if [[ ! -d "$ION_SRC/tests" ]]; then
  echo "ION source tests directory not found: $ION_SRC/tests" >&2
  exit 1
fi

for cmd in ionstop killm bping ionstart; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required ION command not found on PATH: $cmd" >&2
    exit 1
  fi
done

ionstop >/tmp/ion-prestop.log 2>&1 || true

cd "$ION_SRC/tests"
timeout 120 ./runtests bping/

ionstop >/tmp/ion-poststop.log 2>&1 || true

echo
echo "Remaining ION processes:"
pgrep -af '(^|/)(ionadmin|ionclock|rfxclock|bpadmin|bpclock|ipnfw|ipnadminep|udpcli|udpclo|ltpcli|ltpclo|bpecho|bping|bpcounter|bpdriver|ionstart|ionstop|ltpadmin)( |$)' || true
