"""Tier-1 model-exact Monte-Carlo simulator for the DTN AoI/PAoI paper.

Validates the closed forms of the manuscript (Results 1-3, battery hardening)
against stochastic simulation. Stdlib-only (no third-party deps) so it
runs unmodified on any Python 3.8+ host.

Modules:
  residual  -- LEO residual-wait sampling + AoI/PAoI process DES (E1, E2)
  battery   -- energy-queue chain: work-conservation throttle (E9, E10)
  stats     -- replication confidence intervals
"""
