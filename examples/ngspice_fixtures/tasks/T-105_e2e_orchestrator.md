# T-105 — Implement E2E orchestrator

## Objective
Create one command pipeline for fixtures->normalize->query smoke->analyze.

## Scope
- `scripts/e2e.py`
- Stage-wise execution and fail-fast error reporting.

## DoD
- Running e2e command generates all expected outputs.
- Prints concise success/failure summary with artifact paths.
