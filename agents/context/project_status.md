# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- Canonical workflow authority is `playground/agents` with Architect/Executor/Reviewer role files active.
- Shared infrastructure was promoted to repo root: `pdks/` and `libs_common/`.
- Root `libs/` is now the canonical experiment library location.
- Historical archived examples were removed from the active workspace.
- Context scaffolding is initialized under `agents/context/`.
- Agent hydration pack is initialized under `agents/instructions/`.
- `asdl`/`asdlc` toolchain is installed in local `venv` from GitHub.

## Last verified status
- `./venv/bin/python agents/scripts/lint_tasks_state.py` (pending run after latest task updates)

## Next steps (1-3)
1. Execute `T-010` hello-flow experiment on Xyce.
2. Execute `T-011` import/library ergonomics experiment.
3. Execute `T-012` parameter/sweep ergonomics experiment.

## Risks / unknowns
- Xyce availability in this environment is not yet confirmed.
- Run-id and artifact naming conventions need strict enforcement to keep reports reproducible.
- Orchestration requirements may drift without disciplined synthesis into `T-015`.
