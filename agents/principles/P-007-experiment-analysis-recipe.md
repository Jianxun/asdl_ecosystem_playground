# P-007 Experiment Analysis Recipe

## Intent

Each experiment should include a compact, repeatable analysis recipe for future agents.

## Why

- Prevents loss of context between sessions.
- Makes "rerun + verify" a one-command workflow.

## Rules

- Store a short summary in experiment folder with:
  - run command(s)
  - analysis command(s)
  - key formulas
  - expected numerical checkpoints
- Keep path references explicit and run-relative.
- Include at least one machine-readable metrics artifact per run.

## Recommended Artifacts

- `metrics_*.json`
- `plot_*.png`
- `summary_<date>.md`
