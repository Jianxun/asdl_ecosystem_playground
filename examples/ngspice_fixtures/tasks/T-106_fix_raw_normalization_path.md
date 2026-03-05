# T-106 — Fix raw normalization mismatch and validate E2E

## Objective
Make current E2E pipeline pass by fixing fixture RAW generation vs normalizer format handling.

## Scope
- Update fixtures and/or normalizer to support actual produced RAW format.
- Validate complete E2E pipeline.
- Ensure commands use `.venv/` under repo root.

## DoD
- E2E command succeeds (exit 0) from repo root.
- Output artifacts generated across all 3 stages.
- README includes local venv bootstrap + run instructions.
