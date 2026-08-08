"""Energy-queue chain and the work-conservation throttle (sec 6.4).

Battery capacity B units (1 unit = energy for one copy). Harvest per
period A with mean eta = lambda_e * P / e (Poisson by default; the
work-conservation identity needs only the mean). All-or-nothing policy:
at each contact fire k copies iff b >= k.

Embedded chain (pre-fire level b_n):
    b_{n+1} = min(B, (b_n - k*1{b_n >= k}) + A_n)

Throttle p_e(k) = P_pi(b >= k). Validated claims:
    E9  work conservation:  k * p_e = eta - L,  with L = mean per-period
        overflow loss; hence  p_e <= min(1, eta/k).
    E10 k = 1, large B, eta < 1:  p_e = eta  and  P(b = 0) = 1 - eta.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


def poisson(rng: random.Random, mean: float) -> int:
    """Knuth's algorithm for small/moderate means; normal-ish for large."""
    if mean <= 0:
        return 0
    if mean < 30:
        L = math.exp(-mean)
        k = 0
        p = 1.0
        while True:
            k += 1
            p *= rng.random()
            if p <= L:
                return k - 1
    # large mean: round a normal draw (transform method tail is fine here)
    val = int(round(rng.gauss(mean, math.sqrt(mean))))
    return max(0, val)


@dataclass
class BatteryRun:
    p_e: float            # fraction of contacts that fire (b >= k)
    overflow_L: float     # mean per-period harvest lost to the cap
    mean_harvest: float   # measured mean of A (should ~ eta)
    p_zero: float         # fraction of contacts with b == 0
    n: int

    def work_conservation_residual(self, k: int) -> float:
        """|k*p_e - (mean_harvest - L)| -- should be ~0 (E9)."""
        return abs(k * self.p_e - (self.mean_harvest - self.overflow_L))


def simulate_battery(B: int, k: int, eta: float, n_periods: int,
                     seed: int, warmup_periods: int = 0,
                     harvest: str = "poisson") -> BatteryRun:
    """Run the embedded battery chain; return the throttle and diagnostics.

    harvest: 'poisson' (A ~ Poisson(eta)) or 'deterministic'
    (A = round(eta) split to hit mean eta) to show the work-conservation
    identity is distribution-free.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    rng = random.Random(seed)
    b = 0
    fires = 0
    zero = 0
    overflow_total = 0
    harvest_total = 0
    counted = 0
    # for deterministic harvest with non-integer eta, alternate floor/ceil
    det_lo = int(math.floor(eta))
    det_hi = int(math.ceil(eta))
    frac_hi = eta - det_lo  # probability of using ceil to match the mean

    for n in range(n_periods):
        measure = n >= warmup_periods
        fired = b >= k
        if measure:
            counted += 1
            if fired:
                fires += 1
            if b == 0:
                zero += 1
        if fired:
            b -= k
        if harvest == "poisson":
            A = poisson(rng, eta)
        elif harvest == "deterministic":
            A = det_hi if rng.random() < frac_hi else det_lo
        else:
            raise ValueError(f"unknown harvest model: {harvest}")
        if measure:
            harvest_total += A
        nb = b + A
        if nb > B:
            ov = nb - B
            nb = B
        else:
            ov = 0
        if measure:
            overflow_total += ov
        b = nb

    if counted == 0:
        raise ValueError("warmup_periods >= n_periods")
    return BatteryRun(
        p_e=fires / counted,
        overflow_L=overflow_total / counted,
        mean_harvest=harvest_total / counted,
        p_zero=zero / counted,
        n=counted,
    )


def p_e_fluid(k: int, eta: float) -> float:
    """Closed-form balance limit: min(1, eta/k). Upper bound on measured p_e."""
    return min(1.0, eta / k)
