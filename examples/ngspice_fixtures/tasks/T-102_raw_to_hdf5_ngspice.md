# T-102 — Implement ngspice RAW->HDF5 normalizer

## Objective
Implement CLI tool to normalize fixture RAW files into HDF5.

## Scope
- `tools/normalize_raw.py` with function + CLI.
- Preserve vectors and independent variable.
- Emit provenance attrs and basic metadata.

## DoD
- All fixture RAW files convert successfully.
- Output schema follows S-102.
- Add/adjust tests for conversion smoke.
