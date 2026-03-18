# Principles Catalog

These principle files encode reusable agent behaviors for this repository.

Use stable IDs so humans can point to exact guidance in prompts.

## Principles

- `P-001`: `P-001-theory-simulation-correlation.md`
- `P-002`: `P-002-incremental-modular-construction.md`
- `P-003`: `P-003-script-first-analysis.md`
- `P-004`: `P-004-deterministic-validation-first.md`
- `P-005`: `P-005-sign-conventions-and-formulas.md`
- `P-006`: `P-006-observability-driven-probing.md`
- `P-007`: `P-007-experiment-analysis-recipe.md`
- `P-008`: `P-008-close-the-loop-on-guidance.md`
- `P-009`: `P-009-repo-hygiene.md`

## Usage Pattern

- In chat, reference one or more IDs directly (example: "Follow P-001 and P-005 for this task").
- Agent should read referenced files before making changes.
- If a new lesson is discovered, add a new `P-xxx` file and update this index.
