# ION cross-check — residual law in the reference Bundle Protocol implementation

**Status: completed.** A two-node ION-DTN 4.1.4 (BPv7) run over a
scheduled ON/OFF contact plan reproduces the Result-1 residual-wait law
per bundle; recorded output in `results.txt`. The manuscript reports
this as a reference-implementation cross-check (flight-software
lineage), not a sweep.

## What was run

Two ION nodes on one host (UDP convergence layer, loopback), contact
plan = one W=6 s window per P=60 s period (δ=0.10, scaled so a
~1000-bundle run fits in ~1 h wall clock; the law is scale-free in
G²/2P). `bpsource` sends a timestamped bundle every 7.3 s
(incommensurate with P → phase-mixed arrivals); `bpsink` logs receive
epochs. 60 periods → 974 bundles.

## Recorded outcome (`results.txt`)

- **974/974 delivered, zero loss** (store-and-forward over 54 s gaps).
- Mean delay 26.65 s = predicted residual (24.34 s realized-phase mean;
  closed form G²/2P = 24.30 s) **+ a measured dispatch lag of
  2.50 ± 0.51 s** — the model's per-segment service term T_s.
- Delay histogram: ≈δ atom near 0 + uniform slab over (0, G] — the
  mixed residual law; max 57.1 s ≈ G.
- **Non-circular per-bundle check:** regressing measured delay on the
  per-bundle *predicted* residual (from each bundle's send phase) gives
  slope 1.016 (law exact iff 1; tolerance 0.05) with intercept 1.92 s =
  the dispatch lag. At operational periods (P ≈ 5.7×10³ s) that lag is
  ~0.04% of the mean.

## Files

- `gen_plan.py` — emits the `ionadmin` contact-plan commands for a
  given start epoch and period count.
- `node1/`, `node2/` — complete ION config sets (`.ionconfig`,
  `.ionrc`, `.ionsecrc`, `.bprc`, `.ipnrc`): two ipn nodes, UDP
  in/outducts on 127.0.0.1:5551/5552, no crypto.
- `start_ion.sh` / `stop_ion.sh` — bring the pair up (loads
  `global.ionrc` written by `gen_plan.py`) and stop it gracefully
  (node-scoped; no `killm`).
- `run_capture.sh <n_periods> <raw_log> <results_file>` — one full
  experiment: generate plan → start ION → capture `bpsink` with receive
  timestamps → drive `bpsource` on the 7.3 s cadence → stop →
  `summarize.py`.
- `summarize.py` — delay statistics, histogram, phase-decomposition,
  and the per-bundle regression; writes `results.txt`.
- `run_bping_smoke.sh` — optional: ION's own `bping` regression test as
  an install sanity check.
- `results.txt` — the recorded run backing the manuscript's numbers.

## Reproducing

ION-DTN 4.1.4 (tag `ion-open-source-4.1.4`,
github.com/nasa-jpl/ION-DTN), default autotools build, BPv7:

```bash
git clone https://github.com/nasa-jpl/ION-DTN.git ~/src/ION-DTN
cd ~/src/ION-DTN && git checkout ion-open-source-4.1.4
autoreconf -fi && ./configure --prefix=/usr/local
make -j"$(nproc)" && sudo make install && sudo ldconfig
```

Then, from this directory (needs ~65 min wall clock for 60 periods —
the contact plan runs in real time):

```bash
./run_capture.sh 60 delays_raw.log results.txt
```

The scripts are path-relative (`ION_NODE_LIST_DIR` is set to this
directory) and stop only their own two nodes. A short smoke run first:
`./run_capture.sh 5 smoke_raw.log smoke_results.txt`.
