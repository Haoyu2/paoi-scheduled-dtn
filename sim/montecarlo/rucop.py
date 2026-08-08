"""RUCoP-style MDP solver: routing under uncertain contact plans.

Implements the core of RUCoP (Raverta, Fraire et al.): given a contact
plan whose contacts may fail, compute the multi-copy forwarding policy
that maximizes the probability the destination receives a copy, subject
to a copy budget k (max number of simultaneous replicas).

Formulation (holder-set MDP, backward induction over time-ordered
contacts): the state is the set S of nodes currently holding a copy.
Contacts are processed in time order; at contact (f,g,p) with f in S,
g not in S, and |S| < k, the policy may forward (g joins S w.p. p) or
skip; the value is the delivery probability P(dest in S at the end).
Forwarding replicates (sender keeps its copy), as in the Bundle Protocol.

Distinct from our AoI-Energy policy: RUCoP maximizes delivery and is
energy-blind (it will use copies up to the budget whenever they help);
our policy caps copies by the energy threshold k*(eta).
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple


def delivery_prob(contacts: List[Tuple[int, int, float]], source: int,
                  dest: int, k: int) -> float:
    """Max P(dest receives a copy) under a budget of k forward attempts.

    The budget counts transmissions (copies committed), success or fail --
    a copy spent on a failed contact is lost, as in RUCoP. The holder set
    S grows on success; forwarding replicates (sender keeps its copy).
    contacts: time-ordered list of (from, to, success_prob).
    """
    T = len(contacts)

    @lru_cache(maxsize=None)
    def V(i: int, S: frozenset, used: int) -> float:
        if dest in S:
            return 1.0
        if i == T:
            return 0.0
        f, g, p = contacts[i]
        best = V(i + 1, S, used)                 # skip this contact
        if f in S and g not in S and used < k:
            succ = V(i + 1, S | {g}, used + 1)
            fail = V(i + 1, S, used + 1)
            best = max(best, p * succ + (1.0 - p) * fail)
        return best

    return V(0, frozenset({source}), 0)


def min_copies_for_target(contacts, source, dest, target, k_max) -> int:
    """Smallest copy budget whose RUCoP delivery probability reaches the
    confidence target (else k_max). Models CGR-UCoP's confidence-target
    copy selection (energy-blind)."""
    for k in range(1, k_max + 1):
        if delivery_prob(contacts, source, dest, k) >= target:
            return k
    return k_max
