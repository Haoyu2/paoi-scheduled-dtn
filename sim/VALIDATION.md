# Validation matrix (final, as used in the manuscript)

Two-tier plan closed by a reference-implementation cross-check. Every
analytical claim maps to a model-exact Tier-1 experiment; representative
results are corroborated in the DTN-realistic Tier-2 stack (dtnsim:
Bundle Protocol + Contact Graph Routing); the residual-wait anchor is
additionally reproduced in ION. The manuscript's Tier-1 traceability
table mirrors this file.

| Claim (manuscript) | Experiment | Entry point | Result |
|---|---|---|---|
| Residual law, Thm 1 (KS + mean/peak exponents) | E1–E2 | `experiments/e1_residual.py` | KS ≈ 0.002; slopes 1.98/1.00 |
| Phase mixing + failure mode | E3–E6 | `experiments/e3_e6_replication.py` | KS-to-uniform 0.001; locked KS 0.89; Gini gain; ⅔(1−δ) |
| Threshold k\*, unimodality + staircase | E7–E8 | `experiments/e7_e8_threshold.py` | argmin brackets η; saturates at K_max |
| Work conservation, P–K law | E9–E10 | `experiments/e9_battery.py` | ≤1e−5; distribution-free |
| Finite battery downward pressure | E11 | `experiments/e11_finiteB.py` | k\*: 4→2 as B: 64→4 (η=4) |
| Renewal laws + AoI/OPAoI inversion | E12–E13 | `experiments/e12_e13_renewal.py` | E[R] within 1%; crossing at CV²=1+2E[U]/E[V] |
| Ceiling branch, eq. (18) test | E14 | `experiments/e_ceiling.py` | flip at η★ = 3.824 (9/9) |
| Bursty (Markov-modulated) harvest | E15 | `experiments/e15_correlated.py` | k\* invariant to dwell 10; p99 +72%; k=2 at dwell 50 (measured boundary) |
| Uncertainty objective (Prop. 1) | E18 | `experiments/e18_uncertain.py` | ≤0.7%; optimum in candidate set |
| Prop.-1 increment condition grid | — | `experiments/check_gainboundq.py` | min margin 0.067P over 840 (δ,q,η) points |
| Two-candidate policy vs exhaustive | — | `experiments/e_policy.py` | matched at every tested i.i.d.-harvest (η,B) |
| PAoI tail / CCDF closed form | — | `experiments/e_tail.py` | matches eq. (29) pointwise |
| Prediction-error robustness (α) | — | `experiments/e_robust.py` | keep ⌊η⌋; reserve heuristic +50% |
| Matched-budget + adaptive baselines + phase sets | — | `experiments/e_baselines.py` | set-point dominates where energy binds; q=1 oracle tie |
| RUCoP-style MDP core (illustrative) | — | `experiments/e_rucop.py` | concave frontier; 94.7%/40% instance |
| Tier-2 atomic all-or-nothing threshold | — | `tier2/run_r3_atomic.sh` | starvation penalty in real CGR (2.7× at η=1); ties at η≥k fault-free |
| Tier-2 unified (faults + atomic, both metrics) | E16 | `tier2/run_e16_unified.sh` | argmin 1→2→3→3; stall-vs-loss distinction |
| Tier-2 contact-capacity boundary | E17 | `tier2/run_e17_capacity.sh` | flat to ρ=1; step failure beyond |
| Real-ephemeris residual law + pair scan | — | `tier2/make_tle_scenario.py`, `tier2/two_tle_rmin.py` | 0.2%/satellite; residual-min ratio 0.41–0.95 by phase |
| Heterogeneous chain composition (10 seeds) | — | `tier2/run_hetero_seeds.sh` | per-seed ≤5.9%; mean 0.2% |
| ION residual-law cross-check | — | `ion/run_capture.sh` | per-bundle regression slope 1.016; lag = T_s |

Seed counts are experiment-dependent (8–20 for Tier-1 sweeps; 10 for
Tier-2 E16/heterogeneous; 5 for the atomic sweep; 3 for E17) and are
recorded in each results CSV.

Reproduced CSVs can be checked against the frozen paper dataset
(`results/reference/`, `tier2/results/reference/`) with
`python3 sim/compare_results.py [tier2/results]`.
