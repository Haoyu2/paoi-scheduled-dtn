# Tier-1 Monte-Carlo simulator

Model-exact validation of the manuscript's analytical results.
**Stdlib-only — no third-party packages, Python 3.10+.** See
`VALIDATION.md` for the experiment→claim traceability matrix.

## Layout

```
montecarlo/        core library (importable)
  residual.py      LEO residual-wait + AoI/PAoI process DES   (E1, E2)
  battery.py       energy-queue chain, work-conservation       (E9, E10)
  stats.py         replication confidence intervals
experiments/       runnable validation scripts (write CSV to results/)
  e1_residual.py   E1 residual law + E2 provisioning slopes
  e9_battery.py    E9 work conservation + E10 M/D/1 limit
scenarios/         versioned, publishable scenario specs
results/           CSV output (created on first run)
```

## Running (intended on the project VMs)

From this `sim/` directory:

```bash
# fast smoke (seconds) -- confirms the pipeline end to end
python3 experiments/e1_residual.py --quick
python3 experiments/e9_battery.py  --quick

# full runs (minutes; tune --periods/--seeds/--lam for tighter CIs)
python3 experiments/e1_residual.py
python3 experiments/e9_battery.py
```

Each script prints a per-row `OK`/`FAIL` against its pass criteria
(matrix: `VALIDATION.md`) and writes a CSV to `results/`. Time in `residual.py` is normalized to
period `P = 1` (results are dimensionless ratios); the real-seconds
anchor lives in `scenarios/leo_single.yaml`.

## Runtime expectations

Approximate wall-clock times; every process is single-threaded and needs
under 2 GB RAM. Recorded results were produced on Ubuntu (22.04/24.04)
VMs; any modern 4-core/8 GB machine is sufficient.

| Run | Mode | Approx. time | Needs |
|---|---|---|---|
| any Tier-1 experiment `--quick` | smoke | seconds | Python 3.10+ |
| `check_gainboundq.py` | full (analytic grid) | <1 s | Python |
| Tier-1 experiment, full | paper statistics | ~1–15 min each | Python |
| Tier-2 single R1 run | one dtnsim run | <1 min | OMNeT++ + dtnsim |
| `run_e16_unified.sh`, `run_r3_cgr.sh` | full (10 seeds) | ~30–60 min | OMNeT++ + dtnsim |
| `run_r3_atomic.sh`, `run_e17_capacity.sh` | full | ~15–40 min | OMNeT++ + dtnsim |
| `run_hetero_seeds.sh` | full (10 seeds) | ~10 min | OMNeT++ + dtnsim |
| `make_tle_scenario.py`, `two_tle_rmin.py --scan 40` | full | minutes | Python + Skyfield 1.48 |
| ION cross-check (`ion/run_capture.sh 60 ...`) | full | ~65 min (real-time plan) | ION-DTN 4.1.4 |

Scripts write into `results/` (or `tier2/results/`); the committed paper
dataset is frozen under `results/reference/` and `tier2/results/reference/`,
which scripts never touch. Compare a reproduction against the archive:

```bash
python3 compare_results.py               # Tier-1
python3 compare_results.py tier2/results # Tier-2
```

Tier-1 defaults are seed-deterministic and reproduce the reference
bit-for-bit; Tier-2 matches to seed noise given the pinned dtnsim commit.

## What each script checks

- **e1_residual.py** — empirical `E[R]`, `E[R^2]`, atom fraction, and KS
  distance to the mixed residual CDF; then mean AoI / PAoI vs the
  closed forms over a duty-cycle sweep, and the log-log provisioning
  slopes (mean AoI ~2, PAoI ~1 in `(1-delta)`).
- **e9_battery.py** — the work-conservation identity `k*p_e = eta - L`
  (Poisson *and* deterministic harvest, to show it is distribution-free)
  with `p_e <= min(1, eta/k)`; and the `k=1` large-battery limit
  `p_e = eta`, `P(b=0) = 1 - eta`.

## Experiment scripts

- `e1_residual.py` — E1 residual law + E2 provisioning slopes.
- `e3_e6_replication.py` — E3 phase mixing, E4 k=2 Gini gain, E5 same-
  bottleneck, E6 P/2 staggering.
- `e7_e8_threshold.py` — E7 unimodality + k\*, E8 monotonicity/saturation.
- `e9_battery.py` — E9 work conservation + E10 M/D/1 limit.
- `e11_finiteB.py` — E11 finite-battery conservative shift.
- `e12_e13_renewal.py` — E13 renewal residual law + E12 AoI/PAoI inversion.
- `e_ceiling.py` — E14 ceiling branch of the two-candidate rule.
- `e15_correlated.py` — E15 Markov-modulated (bursty) harvest.
- `e18_uncertain.py` — E18 uncertainty objective (Proposition 1).
- `check_gainboundq.py` — Proposition-1 increment condition over a
  (δ, q, η) grid.
- `e_tail.py` — closed-form PAoI tail / CCDF.
- `e_policy.py` — two-candidate policy vs exhaustive search.
- `e_robust.py` — prediction-error (α) robustness.
- `e_baselines.py` — matched-budget, adaptive (greedy/set-point), and
  phase-set baselines.
- `e_rucop.py` — RUCoP-style MDP core (illustrative frontier).

## Status

**Tier-1 complete: all experiments PASS** (recorded results in
`results/*.csv`, figures via `../figs/make_figures.py`). Note
the R3 optimizer is `k*∈{⌊η⌋,⌈η⌉}` (skip-aware), with `⌊η⌋` the
conservative no-starvation rule; E7/E8 used integer η (where they
coincide). The Tier-2 DTN-realistic (dtnsim/CGR) study is in `tier2/`.
