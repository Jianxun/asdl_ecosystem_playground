# S-104 — Analyzer Adapter: HDF5 to prototype modules

## Objective
Run prototype analyzer modules directly from normalized HDF5 artifacts.

## Scope
- Implement `tools/run_analyzers.py`:
  - load HDF5 signal vectors
  - map case types to analyzer modules:
    - square -> edge_events + cycle_extract
    - multitone -> fft_topk
    - ac_onepole -> ac_metrics
- Emit per-case JSON results into `outputs/analysis/<case>.json`.

## Out of Scope
- Auto-discovery for arbitrary circuits.
- Pole-zero model fitting.

## Definition of Done (DoD)
- Analyzer outputs created for all fixture cases.
- Output JSON includes metrics and quality flags.
- Failures are isolated per-case with clear status.
