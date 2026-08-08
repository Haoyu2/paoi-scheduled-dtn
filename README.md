# Peak Age of Information over Scheduled, Energy-Constrained Multi-Segment DTNs: Bundle Replication under Route Uncertainty

Analysis, simulators, scenarios, and manuscript for a freshness (AoI/PAoI)
framework over **scheduled, intermittently connected DTN paths**
(LEO + UAV + terrestrial) with **energy-constrained bundle replication**.

**Project page:** https://uno-networks-lab.github.io/paoi-scheduled-dtn/ ·
**Paper (PDF):** [paper/main.pdf](paper/main.pdf) ·
**Slides:** [slides/paoi-dtn-deck.pdf](slides/paoi-dtn-deck.pdf)

[![smoke](https://github.com/UNO-Networks-Lab/paoi-scheduled-dtn/actions/workflows/smoke.yml/badge.svg)](https://github.com/UNO-Networks-Lab/paoi-scheduled-dtn/actions/workflows/smoke.yml)
[![DOI](https://zenodo.org/badge/1294421871.svg)](https://doi.org/10.5281/zenodo.21841317)

Manuscript prepared for submission to *Digital Communications and Networks*.

## What's here

| Path | Contents |
|---|---|
| `paper/` | LaTeX source + compiled PDF (figures auto-generated from results) |
| `sim/montecarlo/` | Tier-1 model-exact Monte-Carlo simulator (Python, stdlib only) |
| `sim/experiments/` | Tier-1 experiments E1–E18 (residual law, phase mixing, k\*-threshold, battery queue, tails, correlated harvest, uncertainty objective, …) |
| `sim/tier2/` | Tier-2 DTN-realistic experiments: dtnsim (Bundle Protocol + CGR) scenario generators, energy-module & k-copy-router patches, atomic-admission threshold test, real Iridium-NEXT TLE scenarios, constellation pair-phase scan |
| `sim/ion/` | ION-DTN (reference BP implementation) residual-law cross-check: node configs, capture scripts, results |
| `sim/results/`, `sim/tier2/results/` | All CSV results referenced by the paper's figures |
| `sim/VALIDATION.md` | Experiment→claim traceability matrix (what validates which result) |
| `figs/make_figures.py` | Regenerates every auto figure (pgfplots) from the CSVs |
| `slides/` | Presentation deck (pptx + pdf) and its generator |

## Reproducing

**Tier-1 (no dependencies beyond Python 3.10+):**

```bash
cd sim
python3 experiments/e1_residual.py          # Result 1: residual law
python3 experiments/e7_e8_threshold.py      # Result 3: k* threshold + staircase
python3 experiments/e_ceiling.py            # ceiling-branch validation (E14)
python3 experiments/e15_correlated.py       # bursty-harvest robustness (E15)
python3 experiments/e_policy.py             # O(1) two-candidate policy vs optimum
```

Each experiment prints a PASS/CHECK verdict against its closed form and
writes a CSV to `sim/results/`. The committed paper dataset is frozen
under `sim/results/reference/` (and `sim/tier2/results/reference/`),
which scripts never write; after a reproduction run, compare against
the archive with `python3 compare_results.py` (from `sim/`; from the
repository root: `python3 sim/compare_results.py`).

### Experiment-to-command map (manuscript traceability)

| Manuscript experiment | Command (from `sim/`) |
|---|---|
| E1–E2 residual law, AoI/OPAoI vs δ | `python3 experiments/e1_residual.py` |
| E3–E6 phase mixing, two-copy gain | `python3 experiments/e3_e6_replication.py` |
| E7–E8 k\* unimodality, staircase | `python3 experiments/e7_e8_threshold.py` |
| E9–E10 work conservation, M/D/1 limit | `python3 experiments/e9_battery.py` |
| E11 finite-battery k\* vs B | `python3 experiments/e11_finiteB.py` |
| E12–E13 renewal laws, AoI/OPAoI inversion | `python3 experiments/e12_e13_renewal.py` |
| E14 ceiling branch (η★=3.824) | `python3 experiments/e_ceiling.py` |
| E15 Markov-modulated (bursty) harvest | `python3 experiments/e15_correlated.py` |
| E18 uncertainty objective, Prop. 1 / eq. (21) | `python3 experiments/e18_uncertain.py` |
| Policy vs exhaustive optimum | `python3 experiments/e_policy.py` |
| PAoI tail / CCDF | `python3 experiments/e_tail.py` |
| Prediction-error robustness (α) | `python3 experiments/e_robust.py` |
| Matched-budget + adaptive baselines + phase sets | `python3 experiments/e_baselines.py` |
| Increment-condition grid (Prop. 1) | `python3 experiments/check_gainboundq.py` |
| RUCoP-style MDP core | `python3 experiments/e_rucop.py` |
| Tier-2 atomic threshold | `tier2/run_r3_atomic.sh` (on the OMNeT++ host) |
| E16 unified (faults + atomic, both metrics) | `tier2/run_e16_unified.sh` |
| E17 contact-capacity sensitivity | `tier2/run_e17_capacity.sh` |
| Two-TLE pair scan (real ephemeris) | `python3 tier2/two_tle_rmin.py --scan 40` |
| Heterogeneous chain, 10 seeds | `tier2/run_hetero_seeds.sh` |
| ION residual-law cross-check | `ion/run_capture.sh` (see `sim/ion/README.md`) |

The tagged release `v1.0-dcn-submission` corresponds exactly to the
manuscript prepared for DCN submission.

**Tier-2 (dtnsim on OMNeT++ 5.7.1):** build dtnsim, then apply the patches
in `sim/tier2/dtnsim_patch/` (`apply_patch.py` installs the
energy-harvesting battery module; `install_kcopies.py` installs the
CGR-native k-copy router with optional update-atomic admission). Scenario
generators (`make_*_scenario.py`) emit contact plans + omnetpp ini files;
`run_*.sh` scripts run the sweeps. Real-orbit scenarios need `skyfield`
(TLE snapshot included for reproducibility).

**ION cross-check:** `sim/ion/` contains the two-node configs, the
contact-plan generator, capture orchestration, and the summary script
(per-bundle regression of delay on the plan-predicted residual).

**Figures:** `python3 figs/make_figures.py` regenerates
`paper/figures_auto.tex`; the paper compiles with
`pdflatex main.tex` (3 passes).

## Headline results

- Closed-form residual-wait / AoI / peak-age laws for scheduled contacts,
  with an exact AoI/OPAoI inversion threshold
  CV²(V) > 1 + 2E[U]/E[V] — validated to <1% in Monte-Carlo,
  in dtnsim/CGR, on real Iridium-NEXT ephemeris (0.06%), and in ION
  (per-bundle regression slope 1.016).
- Energy–replication threshold k\* = min(K_max, ⌊η⌋ or ⌈η⌉) under
  all-or-nothing firing, with an O(1) two-candidate policy that matched the
  exhaustive optimum at every sampled i.i.d.-harvest energy configuration
  (E15 maps the persistent-harvest boundary where the mean-based rule
  yields); the over-replication
  starvation penalty is reproduced in the real CGR stack (atomic admission:
  k=3 at η=1 is 2.7× worse than single-copy).
- Phase ladder for fixed contact plans: evenly staggered ≤ phase-agnostic
  ≤ locked; on 44 real Iridium pairs the residual-min ratio spans
  0.41–0.95 with pass-phase alignment, quantifying the route set's
  latency-diversity potential — phase-aware copy placement is computable
  from the contact plan.

## Citing

See [CITATION.cff](CITATION.cff); the manuscript is prepared for
submission to *Digital Communications and Networks*. Each release is
archived on Zenodo under concept DOI
[10.5281/zenodo.21841317](https://doi.org/10.5281/zenodo.21841317) (resolves to the latest
version).

## License

Original software, scripts, and experiment-result data in this repository
are released under the MIT License (see [LICENSE](LICENSE)). The manuscript,
slides, and their figures remain © the authors. dtnsim and ION-DTN are
third-party projects, not redistributed here; the committed TLE snapshot
derives from CelesTrak GP data (see
[sim/tier2/TLE_PROVENANCE.md](sim/tier2/TLE_PROVENANCE.md)).
