# S-105 — End-to-End Regression Orchestrator

## Objective
Provide a single command to run simulate -> normalize -> query-smoke -> analyze.

## Scope
- Implement `scripts/e2e.py` (or equivalent) to orchestrate:
  1) ngspice fixture runs
  2) RAW->HDF5 normalization
  3) HDF5 query smoke checks
  4) analyzer adapter execution
- Fail-fast behavior with concise error summary.

## Out of Scope
- CI integration with remote services.

## Definition of Done (DoD)
- One command generates all expected artifacts under `outputs/`.
- Non-zero exit on failures; clear stage attribution.
- Success summary prints artifact locations.
