# TLE provenance — `iridium.tle`

The real-ephemeris experiments (`make_tle_scenario.py`,
`two_tle_rmin.py`) use the two-line-element snapshot committed here as
`iridium.tle`, so their results are reproducible bit-for-bit without a
network fetch. TLEs age; re-fetching gives *different* (current)
orbits, which changes pass times and the pairwise phase alignments —
use the committed file to reproduce the recorded results.

- **Source:** CelesTrak GP query
  `https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=tle`
- **Retrieved:** 2026-06-24 (UTC)
- **Contents:** 80 Iridium-NEXT satellites; element epochs span
  26174.30358829–26175.30892826 (days 174–175 of 2026, i.e. all within
  ~24 h of retrieval)
- **SHA-256 (`iridium.tle`):**
  `b07391580688cc41057e088bc0a23ab139bc30d12a284b43e6ae39a7c822dbd1`
- **Propagator:** Skyfield 1.48 (SGP4), `skyfield>=1.48` in
  `../../requirements.txt`; results recorded with 1.48 exactly
- **Ground station:** Svalbard, 78.23° N, 15.39° E (chosen for dense
  polar-orbit pass coverage)
- **Visibility rule:** contact open while elevation ≥ 10°, sampled on
  the generator's fixed time grid; 7-day horizon → 101 passes for the
  single-satellite scenario
- **Derived artifacts:** `contactPlan/` scenario plans, the recorded
  `results/tle_summary.txt` (single-satellite residual-law check) and
  `results/two_tle_scan.log` (44-pair residual-min scan)

`make_tle_scenario.py` only downloads when `iridium.tle` is absent;
deleting the file re-fetches current elements (not reproducible —
intentionally not the default).
