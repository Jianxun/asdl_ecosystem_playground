# T-104 — Implement analyzer adapter over HDF5

## Objective
Wire normalized HDF5 signals into prototype analyzers and emit per-case results.

## Scope
- `tools/run_analyzers.py` with case presets for square/multitone/ac_onepole.
- Save results to `outputs/analysis/*.json`.

## DoD
- All target analyzers run on relevant fixture cases.
- Result JSON includes metrics + quality.
