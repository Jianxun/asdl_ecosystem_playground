# Codebase Map

## Directories
- `agents/`: canonical workflow system for this repo.
- `agents/roles/`: Architect, Executor, Reviewer role contracts.
- `agents/context/`: project working memory and migration notes.
- `agents/instructions/`: hydration pack for future agents (quickstart/workflow/debugging/snippets).
- `agents/prompts/workflows/`: workflow prompts (including ExecPlan prompt contract).
- `agents/plans/`: active execution plan documents.
- `agents/scripts/`: workflow scripts (dispatcher helpers, ingestion helpers).
- `agents/tools/opencode_session_pipeline/`: OpenCode session ingest/normalize/validate/query pipeline.
- `agents/scratchpads/`: per-task notes (`T-00X_*.md`).
- `archive/`: repo-root telemetry archive for OpenCode session raw logs, canonical events, indexes, and checkpoints.
- `labs/`: canonical teaching labs (one lab per subdirectory).
- `libs_common/`: shared ASDL sources for common primitives/simulation helpers.
- `pdks/`: PDK models and ASDL wrappers.
- `examples/`: legacy/reference scratch assets.
- `analysis/`: scripts for metric extraction and result analysis.
- `analysis/tools/ngspice/`: canonical ngspice RAW normalization tools.
- `docs/`: reports, templates, and workflow guidance.
- `labs/<lab-id>/artifacts/`: generated lab outputs (expected git-ignored by extension).

## Quick Reference: Workflow
- `agents/roles/architect.md`: project planning/contract authority.
- `agents/roles/executor.md`: implementation task execution protocol.
- `agents/roles/reviewer.md`: review/merge closeout protocol.
- `agents/context/github_issues_task_tracking.md`: canonical issue label/state workflow.
- `agents/scripts/new_execplan.py`: creates an ExecPlan scaffold under `agents/plans/`.
- `agents/scripts/run_opencode_ingestion.sh`: canonical one-command session ingest -> normalize -> validate.

## Quick Reference: Configuration
- `.asdlrc`: project-level backend config/lib roots/env wiring.
- `config/backends.yaml`: backend template definitions.

## Quick Reference: Shared Libraries
- `libs_common/analoglib.asdl`: common analog source/passive device definitions.
- `libs_common/simulation.ngspice.asdl`: simulation directive device definitions.

## Quick Reference: PDK Assets
- `pdks/gf180mcu/asdl/`: ASDL-facing PDK library entrypoints.
- `pdks/gf180mcu/ngspice/`: ngspice model/include assets.
- `pdks/gf180mcu/xyce/`: xyce model/include assets.
