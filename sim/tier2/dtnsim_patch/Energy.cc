#include "src/node/energy/Energy.h"

Define_Module(Energy);

void Energy::initialize()
{
    enable_ = par("enable").boolValue();
    atomic_ = par("atomic").boolValue();
    harvestRate_ = par("harvestRate").doubleValue();
    cost_ = par("perCopyCost").doubleValue();
    capacity_ = par("batteryCapacity").doubleValue();
    battery_ = par("batteryInit").doubleValue();
    lastUpdate_ = simTime();
}

void Energy::handleMessage(cMessage *msg)
{
    // No self-messages; harvesting is computed lazily in refresh().
    delete msg;
}

void Energy::refresh()
{
    simtime_t now = simTime();
    double dt = (now - lastUpdate_).dbl();
    if (dt > 0) {
        battery_ += harvestRate_ * dt;
        if (battery_ > capacity_)
            battery_ = capacity_;
        lastUpdate_ = now;
    }
}

bool Energy::available()
{
    if (!enable_ || atomic_)
        return true;
    refresh();
    return battery_ >= cost_;
}

void Energy::consume()
{
    if (!enable_ || atomic_)
        return;
    refresh();
    battery_ -= cost_;
    spent_ += cost_;
    if (battery_ < 0)
        battery_ = 0;
}

bool Energy::atomicMode()
{
    return enable_ && atomic_;
}

bool Energy::tryConsumeCopies(int n)
{
    if (!enable_)
        return true;
    refresh();
    double need = n * cost_;
    if (battery_ >= need) {
        battery_ -= need;
        admitted_++;
        spent_ += need;
        return true;
    }
    skipped_++;
    return false;   // ALL-OR-NOTHING: no partial spend
}

void Energy::finish()
{
    // Exact admission bookkeeping for post-processing (E16):
    // admitted updates (k copies each), skipped updates, energy spent.
    recordScalar("energyAdmittedUpdates", admitted_);
    recordScalar("energySkippedUpdates", skipped_);
    recordScalar("energySpent", spent_);
}
