package src.node.energy;

// Energy-harvesting battery for a node (Result 3 / sec 6.3-6.4).
// Gates transmissions: a node can forward a copy only if battery >= e,
// and each forwarded copy costs e; battery recharges at harvestRate.
// enable=false => unlimited energy (legacy behaviour, no gating).
//
// atomic=true (with enable=true) switches to ALL-OR-NOTHING admission:
// energy is charged once per update at the source-routing replication
// point (k units for a k-copy update, via tryConsumeCopies(k) called by
// RoutingCgrModelKCopies), and the per-transmission gate/decrement in
// Dtn.cc becomes a no-op (available() -> true, consume() -> nothing).
// This prevents double-charging admitted copies and never blocks the
// transmission of an already-paid copy.
simple Energy
{
    parameters:
        @display("i=block/cogwheel");
        bool enable = default(false);
        bool atomic = default(false);           // all-or-nothing per-update admission
        double harvestRate = default(0);        // lambda_e: energy units per second
        double perCopyCost = default(1);        // e: energy per forwarded copy
        double batteryCapacity = default(1e12); // B: battery cap (units)
        double batteryInit = default(0);        // initial battery (units)
}
