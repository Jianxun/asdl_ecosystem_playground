# Codebase Map

## Directories
- `agents/`: canonical workflow system for this repo.
- `agents/roles/`: Architect, Executor, Reviewer role contracts.
- `agents/context/`: project working memory and consolidated task metadata/state.
- `agents/instructions/`: hydration pack for future agents (quickstart/workflow/debugging/snippets).
- `agents/prompts/workflows/`: workflow prompts (including ExecPlan prompt contract).
- `agents/plans/`: active execution plan documents.
- `agents/scripts/`: workflow scripts (`lint_tasks_state.py`, dispatcher helpers).
- `agents/scratchpads/`: per-task notes (`T-00X_*.md`).
- `labs/`: canonical teaching labs (one lab per subdirectory).
- `libs_common/`: shared ASDL sources for common primitives/simulation helpers.
- `pdks/`: PDK models and ASDL wrappers.
- `examples/`: legacy/reference scratch assets.
- `analysis/`: scripts for metric extraction and result analysis.
- `analysis/tools/xyce/`: canonical Xyce post-processing tools (`raw_to_h5.py`, `format_xyce_op_csv.py`).
- `docs/`: reports, templates, and workflow guidance.
- `labs/<lab-id>/artifacts/`: generated lab outputs (expected git-ignored by extension).

## Quick Reference: Workflow
- `agents/roles/architect.md`: project planning/contract authority.
- `agents/roles/executor.md`: implementation task execution protocol.
- `agents/roles/reviewer.md`: review/merge closeout protocol.
- `agents/scripts/lint_tasks_state.py`: consolidated task metadata/state linter.
- `agents/scripts/new_execplan.py`: creates an ExecPlan scaffold under `agents/plans/`.

## Quick Reference: Configuration
- `.asdlrc`: project-level backend config/lib roots/env wiring.
- `config/backends.yaml`: backend template definitions.

## Quick Reference: Shared Libraries
- `libs_common/analoglib.asdl`: common analog source/passive device definitions.
- `libs_common/simulation.xyce.asdl`: simulation directive device definitions.

## Quick Reference: PDK Assets
- `pdks/gf180mcu/asdl/`: ASDL-facing PDK library entrypoints.
- `pdks/gf180mcu/ngspice/`: ngspice model/include assets.
- `pdks/gf180mcu/xyce/`: xyce model/include assets.
