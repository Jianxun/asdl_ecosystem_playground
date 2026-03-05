# S-102 — RAW→HDF5 Normalizer (ngspice-focused)

## Objective
Normalize ngspice RAW outputs into a stable HDF5 structure for downstream querying and analysis.

## Scope
- Implement `tools/normalize_raw.py` (CLI + importable function).
- Inputs: RAW file path, output HDF5 path, optional metadata (case_id, simulator).
- Output HDF5 groups/datasets:
  - `vectors`
  - `vector_names`
  - `vector_kinds` (if available)
  - `indep_var`
  - `signals` (flat v1 acceptable)
- Include quality metadata attrs and source provenance.

## Out of Scope
- Universal RAW dialect support.
- Multi-step sweep-in-one-file handling.

## Definition of Done (DoD)
- All S-101 fixture RAW files normalize without errors.
- Integrity checks pass (shape consistency, independent variable present).
- CLI usage documented in README or docs snippet.
