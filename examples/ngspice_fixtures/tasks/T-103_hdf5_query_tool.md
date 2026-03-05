# T-103 — Implement HDF5 query tool

## Objective
Provide compact query operations for normalized HDF5 artifacts.

## Scope
- `tools/h5_query.py` with subcommands: list-signals, summary, head, range.
- JSON output by default.

## DoD
- Query commands work on normalized fixture files.
- Missing signal/range errors are clear.
