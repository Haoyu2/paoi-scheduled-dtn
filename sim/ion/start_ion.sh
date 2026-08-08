#!/usr/bin/env bash
# Start both ION nodes and load the contact plan (global.ionrc must exist).
set -e
cd "$(dirname "$0")"
export ION_NODE_LIST_DIR=$PWD
export PATH=/usr/local/bin:$PATH
rm -f ion_nodes

cd node1
ionadmin node1.ionrc
sleep 1
ionadmin ../global.ionrc
sleep 1
ionsecadmin node1.ionsecrc
sleep 1
bpadmin node1.bprc
sleep 1

cd ../node2
ionadmin node2.ionrc
sleep 1
ionadmin ../global.ionrc
sleep 1
ionsecadmin node2.ionsecrc
sleep 1
bpadmin node2.bprc
sleep 1
echo "ION nodes 1 and 2 started."
