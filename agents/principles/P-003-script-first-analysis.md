# P-003 Script-First Analysis

## Intent

Prefer reusable analysis scripts over one-shot terminal snippets for any metric that may be needed again.

## Why

- Improves handoff between sessions and agents.
- Makes analysis reproducible and auditable.
- Reduces repeated mistakes in ad hoc calculations.

## Rules

- If a metric is used more than once (or likely to be reused), implement it in `analysis/tools/xyce/`.
- Scripts should accept explicit input path(s) and emit explicit output artifact(s).
- Keep outputs machine-readable where possible (`.json`, `.csv`) and optionally plots (`.png`).
- Keep formulas in code comments or docstrings when sign/orientation is non-obvious.

## Minimum Script Contract

- Inputs: run directory or file paths.
- Outputs: named metrics file and any plots.
- Exit non-zero for missing required files.
- Print concise success line with output paths.
