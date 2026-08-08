"""Alternating-renewal ON/OFF gating: UAV & terrestrial residual law (sec 6.5).

One model covers all segment types via the OFF-gap distribution V:
  deterministic  -> LEO (recovers Result 1)
  gamma(CV<1)    -> UAV semi-periodic (jitter)
  exponential    -> UAV/terrestrial 2-state CTMC (CV=1)
  pareto(CV>1)   -> terrestrial heavy-tailed (inversion regime)

Residual law (sec 6.5):
    P(R=0) = E[U]/E[C],  f_R(r) = P(V>r)/E[C] (r>0),
    E[R]   = E[V^2]/(2 E[C]),
    PAoI   = T_s + E[V],   mean AoI = T_s + E[V^2]/(2 E[C]).
Inversion (PAoI < mean AoI)  <=>  E[V^2] > 2 E[C] E[V]  -> CV^2(V) > 1.
"""
from __future__ import annotations

import bisect
import math
import random
from dataclasses import dataclass
from typing import Callable, List, Tuple


def gap_sampler(kind: str, G: float, cv: float = None) -> Callable[[random.Random], float]:
    """Return f(rng) -> OFF-gap sample with mean G and the requested CV."""
    if kind == "det":
        return lambda rng: G
    if kind == "exp":
        return lambda rng: rng.expovariate(1.0 / G)
    if kind == "gamma":
        if cv is None or cv <= 0:
            raise ValueError("gamma needs cv > 0")
        k = 1.0 / (cv * cv)          # shape; k>1 -> CV<1, k<1 -> CV>1
        theta = G * cv * cv          # scale; mean = k*theta = G
        return lambda rng: rng.gammavariate(k, theta)
    if kind == "pareto":
        if cv is None or cv <= 0:
            raise ValueError("pareto needs cv > 0")
        a = 1.0 + math.sqrt(1.0 + 1.0 / (cv * cv))   # alpha, gives CV(V)=cv, var finite
        xm = G * (a - 1.0) / a                        # mean = a*xm/(a-1) = G
        return lambda rng: xm / (rng.random() ** (1.0 / a))
    raise ValueError(f"unknown gap kind: {kind}")


@dataclass
class RenewalResidual:
    mean_R: float
    atom_frac: float       # empirical P(R=0)
    mean_R_cf: float       # E[V^2]/(2 E[C]) from the sampled gaps
    atom_cf: float         # U/E[C]
    n: int


def residual_law(samp: Callable, U: float, n_cycles: int, n_arrivals: int,
                 seed: int) -> RenewalResidual:
    """Sample residual waits over an alternating ON(U)/OFF(V) timeline."""
    rng = random.Random(seed)
    Vs = [samp(rng) for _ in range(n_cycles)]
    starts: List[float] = []
    t = 0.0
    for V in Vs:
        starts.append(t)
        t += U + V
    T = t
    Rs = []
    for _ in range(n_arrivals):
        a = rng.uniform(0.0, T)
        i = bisect.bisect_right(starts, a) - 1
        off = a - starts[i]
        Rs.append(0.0 if off < U else Vs[i] - (off - U))
    n = len(Rs)
    mean_R = sum(Rs) / n
    atom = sum(1 for r in Rs if r == 0.0) / n
    EV2 = sum(v * v for v in Vs) / len(Vs)
    EC = U + sum(Vs) / len(Vs)
    return RenewalResidual(mean_R, atom, EV2 / (2 * EC), U / EC, n)


@dataclass
class RenewalAoI:
    mean_aoi: float
    mean_paoi: float
    EV: float
    EV2: float
    EC: float

    @property
    def predicted_inversion(self) -> bool:
        return self.EV2 > 2 * self.EC * self.EV

    @property
    def observed_inversion(self) -> bool:
        return self.mean_paoi < self.mean_aoi


def aoi_paoi(samp: Callable, U: float, T_s: float, n_cycles: int,
             seed: int) -> RenewalAoI:
    """Generate-at-will AoI/PAoI over the renewal gating (sec 6.5 closed form)."""
    rng = random.Random(seed)
    Vs = [samp(rng) for _ in range(n_cycles)]
    n = len(Vs)
    sumC = sum(U + V for V in Vs)
    area = T_s * sumC + sum(V * V / 2.0 for V in Vs)
    EV = sum(Vs) / n
    EV2 = sum(V * V for V in Vs) / n
    EC = sumC / n
    return RenewalAoI(area / sumC, T_s + EV, EV, EV2, EC)
