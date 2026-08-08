#!/usr/bin/env bash
# Graceful stop of the two ion-r1 nodes only (no killm -- other software runs on this VM).
cd "$(dirname "$0")"
export ION_NODE_LIST_DIR=$PWD
export PATH=/usr/local/bin:$PATH
for d in node1 node2; do
  ( cd "$d" && bpadmin . ; sleep 2 ; ionadmin . ) || true
  sleep 2
done
echo "ion-r1 nodes stopped."
