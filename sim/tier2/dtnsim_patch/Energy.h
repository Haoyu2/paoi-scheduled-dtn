#ifndef SRC_NODE_ENERGY_ENERGY_H_
#define SRC_NODE_ENERGY_ENERGY_H_

#include <omnetpp.h>
using namespace omnetpp;

// Per-node energy-harvesting battery. See Energy.ned.
class Energy : public cSimpleModule
{
public:
    // True if a copy can be sent now (battery >= e); harvests up to now.
    // Always true when disabled (unlimited energy) OR in atomic mode
    // (energy was already charged at admission; per-transmission gating
    // would double-gate).
    bool available();
    // Consume one copy's energy (no-op when disabled or in atomic mode;
    // atomic admission charges via tryConsumeCopies() instead).
    void consume();
    // True if this node uses all-or-nothing per-update admission.
    bool atomicMode();
    // Atomic all-or-nothing spend: if battery >= n * perCopyCost, deduct
    // it and return true; else deduct NOTHING and return false. Always
    // true (free) when the module is disabled.
    bool tryConsumeCopies(int n);

protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    // Record admission bookkeeping scalars (energyAdmittedUpdates,
    // energySkippedUpdates, energySpent) so post-processing can read the
    // exact admitted-update count from the .sca (E16). Purely additive.
    virtual void finish() override;

private:
    void refresh();              // accrue harvest since lastUpdate_
    bool enable_ = false;
    bool atomic_ = false;
    double harvestRate_ = 0;
    double cost_ = 1;
    double capacity_ = 1e12;
    double battery_ = 0;
    simtime_t lastUpdate_;
    long admitted_ = 0;          // atomic updates admitted (tryConsumeCopies ok)
    long skipped_ = 0;           // atomic updates rejected (whole update skipped)
    double spent_ = 0;           // total energy units actually deducted
};

#endif /* SRC_NODE_ENERGY_ENERGY_H_ */
