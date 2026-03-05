# S-103 — HDF5 Query Tool (agent-facing)

## Objective
Provide compact, scriptable HDF5 queries so agents can inspect data without loading full traces.

## Scope
- Implement `tools/h5_query.py` with subcommands:
  - `list-signals`
  - `summary`
  - `head --signal <name> --n <k>`
  - `range --signal <name> --x0 --x1`
- Default output JSON; optional plain text.

## Out of Scope
- Plot rendering.
- SQL engine embedding.

## Definition of Done (DoD)
- Commands work on all normalized fixture HDF5 files.
- Outputs are compact and machine-readable.
- Error messages are actionable for missing signals/ranges.
