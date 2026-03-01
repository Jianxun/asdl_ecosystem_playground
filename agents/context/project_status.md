# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- Canonical workflow authority is `playground/agents` with Architect/Executor/Reviewer role files active.
- Shared infrastructure was promoted to repo root: `pdks/` and `libs_common/`.
- Root `libs/` is now the canonical experiment library location.
- Historical archived examples were removed from the active workspace.
- Context scaffolding is initialized under `agents/context/`.

## Last verified status
- `./venv/bin/python agents/scripts/lint_tasks_state.py` (pending run in this session)

## Next steps (1-3)
1. Execute `T-001` to enforce source/generated boundaries and keep `libs/` source-only.
2. Execute `T-002` to land first end-to-end smoke experiment flow.
3. Execute `T-003` to automate experiment run/report scaffolding.

## Risks / unknowns
- Current `libs/` may still include generated artifacts from copied examples.
- Backend/simulator availability in the local environment is not yet baseline-checked.
- Inconsistent experiment naming conventions may reduce reproducibility if not standardized early.
