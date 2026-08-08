#!/usr/bin/env python3
"""Install a CGR-native k-copy router (RoutingCgrModelKCopies) into dtnsim.

Derives the new router from RoutingCgrModel350_2Copies (which already
contains the full CGR machinery: identifyProximateNodes, cgrForward,
enqueueToNeighbor, ...). The only change is routeAndQueueBundle: instead
of one copy (or AT-vs-hops 2 copies), it enqueues a copy to each of the
top-k DISTINCT proximate next-hops ranked by the CGR criteria -- i.e.
k copies over the k best decorrelated CGR routes. Copy count = the
'bundlesCopies' NED parameter.

ATOMIC ALL-OR-NOTHING ENERGY ADMISSION (Result 3): when the node's
Energy module has enable=true AND atomic=true, a fresh update at its
source (hop 0, first routing) is launched with exactly k copies iff the
battery holds >= k*perCopyCost energy units -- charged atomically in one
shot via Energy::tryConsumeCopies(k). Otherwise the WHOLE update is
skipped (bundle deleted, zero spend; no partial replication, no
deferral). Double-charge avoidance: in atomic mode the Energy module's
per-transmission hooks in Dtn.cc are no-ops (available() -> true,
consume() -> nothing), so admission is the only place energy is spent;
the paid_ set additionally guards against re-charging an admitted
hop-0 bundle that bounces through limbo and is re-routed.

Idempotent. Run on the VM with the dtnsim src dir:
    python3 install_kcopies.py ~/dtnsim/dtnsim/src
"""
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/dtnsim/dtnsim/src")
RD = os.path.join(SRC, "node", "dtn", "routing")

NEW_METHOD = r"""void RoutingCgrModelKCopies::routeAndQueueBundle(BundlePkt * bundle, double simTime)
{
	if (!printDebug_)
		cout.setstate(std::ios_base::failbit);

	dijkstraCalls = 0;
	dijkstraLoops = 0;
	tableEntriesExplored = 0;

	// Is this a fresh update being launched at its source? (hop 0 and
	// never routed/replicated before; limbo/contact-end re-routes of
	// already-launched copies do not count.)
	long bid = bundle->getBundleId();
	bool sourceLaunch = (bundle->getHopCount() == 0 && replicated_.count(bid) == 0);

	// ALL-OR-NOTHING atomic energy admission (Result 3): a fresh update
	// is launched with exactly kCopies_ copies iff the source battery
	// holds >= kCopies_ * perCopyCost units, charged here in one shot;
	// otherwise the WHOLE update is skipped (bundle deleted, zero
	// spend). Skipped updates never enter the SDR, so a plain delete is
	// the correct disposal (same in-router delete-and-return pattern as
	// RoutingSprayAndWait; Dtn::dispatchBundle does not touch the bundle
	// after routing->msgToOtherArrive()). In atomic mode the Energy
	// module's per-transmission gate/decrement in Dtn.cc are no-ops, so
	// energy is charged exactly once per admitted update: k units here.
	if (sourceLaunch)
	{
		Energy * energyMod = check_and_cast<Energy *>(dtn_->getParentModule()->getSubmodule("energy"));
		if (energyMod->atomicMode() && paid_.count(bid) == 0)
		{
			if (!energyMod->tryConsumeCopies(kCopies_))
			{
				delete bundle;          // skip the whole update
				if (!printDebug_)
					cout.clear();
				return;
			}
			paid_.insert(bid);          // never re-charge on limbo re-route
		}
	}

	// Identify all proximate next-hops with a CGR route to the destination.
	vector<ProximateNode> proximateNodes;
	vector<int> excludedNodes;
	if (bundle->getReturnToSender() == false)
		excludedNodes.push_back(bundle->getSenderEid());
	identifyProximateNodes(bundle, simTime, excludedNodes, &proximateNodes, arrivalTime);

	if (proximateNodes.empty())
	{
		enqueueToLimbo(bundle);
		if (!printDebug_) cout.clear();
		return;
	}

	// Rank by CGR criteria: confidence desc, arrival time asc, hops asc, node asc.
	std::sort(proximateNodes.begin(), proximateNodes.end(),
		[](const ProximateNode &a, const ProximateNode &b) {
			if (a.confidence != b.confidence) return a.confidence > b.confidence;
			if (a.arrivalTime != b.arrivalTime) return a.arrivalTime < b.arrivalTime;
			if (a.hopCount != b.hopCount) return a.hopCount < b.hopCount;
			return a.neighborNodeNbr < b.neighborNodeNbr;
		});

	// Replicate only at the source (which pays the energy); intermediate
	// nodes forward a single best copy. This bounds total copies to k and
	// avoids per-hop copy explosion.
	// Replicate exactly once per origin bundle: only at the source (hop 0)
	// and only the first time it is routed (limbo re-routes must not
	// re-replicate). All enqueued copies are marked so they never replicate.
	int copies = sourceLaunch ? kCopies_ : 1;

	// Enqueue a copy to each of the top-k DISTINCT next-hops.
	std::set<int> usedNeighbors;
	int sent = 0;
	for (size_t i = 0; i < proximateNodes.size() && sent < copies; i++)
	{
		int nb = proximateNodes[i].neighborNodeNbr;
		if (usedNeighbors.count(nb)) continue;
		usedNeighbors.insert(nb);
		BundlePkt * b = (sent == 0) ? bundle : bundle->dup();
		if (sent > 0)
			b->setBundleId(b->getId());   // unique id per copy: avoid SDR collision
		replicated_.insert(b->getBundleId());   // mark: never replicate again
		ProximateNode pn = proximateNodes[i];
		enqueueToNeighbor(b, &pn);
		sent++;
	}
	if (sent == 0)
		enqueueToLimbo(bundle);

	if (!printDebug_)
		cout.clear();
}
"""


def transform_h(s):
    s = s.replace("RoutingCgrModel350_2Copies", "RoutingCgrModelKCopies")
    s = s.replace("SRC_NODE_DTN_ROUTINGCGRMODEL_PROACTIVE_H_",
                  "SRC_NODE_DTN_ROUTINGCGRMODEL_KCOPIES_H_")
    s = s.replace("#include <src/node/dtn/routing/CgrRoute.h>",
                  "#include <set>\n#include <src/node/dtn/routing/CgrRoute.h>", 1)
    s = s.replace("bool printDebug, cModule * dtn);",
                  "bool printDebug, cModule * dtn, int kCopies);")
    s = s.replace("\tcModule * dtn_;",
                  "\tcModule * dtn_;\n\tint kCopies_ = 2;\n\tstd::set<long> replicated_;"
                  "\n\tstd::set<long> paid_;   // atomic admission already charged (guards limbo re-routes)")
    return s


def transform_cc(s):
    s = s.replace("RoutingCgrModel350_2Copies", "RoutingCgrModelKCopies")
    s = s.replace('#include "RoutingCgrModelKCopies.h"',
                  '#include "RoutingCgrModelKCopies.h"\n#include <set>\n#include <algorithm>\n'
                  '#include "src/node/energy/Energy.h"', 1)
    # constructor: add kCopies param + assignment (note: no space after comma in .cc)
    s = s.replace("bool printDebug,cModule * dtn) :",
                  "bool printDebug, cModule * dtn, int kCopies) :")
    s = s.replace("\tprintDebug_ = printDebug;\n\tdtn_ = dtn;\n}",
                  "\tprintDebug_ = printDebug;\n\tdtn_ = dtn;\n\tkCopies_ = kCopies;\n}")
    # swap in the new routeAndQueueBundle (up to the cgrForward definition)
    start = s.index("void RoutingCgrModelKCopies::routeAndQueueBundle")
    end = s.index("RoutingCgrModelKCopies::ProximateNode* RoutingCgrModelKCopies::cgrForward")
    s = s[:start] + NEW_METHOD + "\n\n" + s[end:]
    return s


def patch_dtn(src):
    p = os.path.join(src, "node", "dtn", "Dtn.cc")
    s = open(p).read()
    if "RoutingCgrModelKCopies" in s:
        print("Dtn.cc already has KCopies")
        return
    s = s.replace('#include "src/node/energy/Energy.h"',
                  '#include "src/node/energy/Energy.h"\n#include "src/node/dtn/routing/RoutingCgrModelKCopies.h"', 1)
    anchor = ('else if (routeString.compare("cgrModel350_2Copies") == 0)\n'
              '\t\t\trouting = new RoutingCgrModel350_2Copies(eid_, &sdr_, &contactPlan_, par("printRoutingDebug"), this);')
    add = (anchor +
           '\n\t\telse if (routeString.compare("cgrModelKCopies") == 0)\n'
           '\t\t{\n\t\t\tint bundlesCopies = par("bundlesCopies");\n'
           '\t\t\trouting = new RoutingCgrModelKCopies(eid_, &sdr_, &contactPlan_, par("printRoutingDebug"), this, bundlesCopies);\n'
           '\t\t}')
    assert anchor in s, "2Copies factory anchor not found"
    s = s.replace(anchor, add)
    open(p, "w").write(s)
    print("Dtn.cc patched (factory + include)")


def main():
    h = transform_h(open(os.path.join(RD, "RoutingCgrModel350_2Copies.h")).read())
    cc = transform_cc(open(os.path.join(RD, "RoutingCgrModel350_2Copies.cc")).read())
    open(os.path.join(RD, "RoutingCgrModelKCopies.h"), "w").write(h)
    open(os.path.join(RD, "RoutingCgrModelKCopies.cc"), "w").write(cc)
    print("wrote RoutingCgrModelKCopies.{h,cc}")
    patch_dtn(SRC)


if __name__ == "__main__":
    main()
