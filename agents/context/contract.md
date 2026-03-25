# Contract

## Project overview
ASDL Playground is a lab-driven repository for exercising the ASDL authoring-to-simulation workflow end to end. The primary goal is to teach circuit concepts through reproducible labs while stress testing language semantics, compiler/emission behavior, simulator integration, and analysis workflows.

The repository is intentionally split between infrastructure (`pdks/`, `libs_common/`, backend config) and lab content (`labs/`). The `agents/` workflow is the canonical operating model for planning, execution, review, and context continuity.

## System boundaries / components
- `agents/`: canonical agent workflow (roles, context, scripts, scratchpads, logs).
- `labs/`: teaching labs; one lab per subdirectory.
- `libs_common/`: shared reusable ASDL blocks (for example sources and simulation directives).
- `pdks/`: PDK wrappers and simulator model assets used by labs.
- `examples/`: legacy/reference assets (config/docs/scratch), not the primary authoring location.
- `analysis/`: post-processing scripts and metric extraction.
- `docs/`: project-level reports and playbooks.
- `labs/<lab-id>/artifacts/`: generated per-lab outputs (netlists/logs/raw/HDF5), git-ignored by extension patterns.

## Interfaces & data contracts
- Project config is driven by repo-root `.asdlrc`.
- `.asdlrc` sets:
  - `backend_config: ${ASDLRC_DIR}/config/backends.yaml`
  - `lib_roots`: `${ASDLRC_DIR}/pdks/${PDK}/asdl`, `${ASDLRC_DIR}/libs_common`, `${ASDLRC_DIR}/libs`
  - `env` variables for `PDK`, `PDK_PATH`, `PDK_ASDL_PATH`, `ASDL_DESIGN_LIBS_PATH`, and `ASDL_LIB_PATH`.
- Task planning and status contracts:
  - GitHub Issues are the task metadata + runtime state source of truth.
  - Active task issues include `ExecPlan Path` pointing to `agents/plans/<slug>.md`.
  - Canonical task-state labels: `task:ready`, `task:in_progress`, `task:blocked`, `task:ready_for_review`, `task:review_in_progress`, `task:done`.
  - ExecPlan format and policy are defined in `agents/prompts/workflows/execplan.md`.
  - Legacy `agents/context/tasks*.yaml` files are archived history only.

## Invariants
- `agents/` workflow is canonical for project execution and handoff.
- New lab source lives in `labs/`; do not create new canonical lab source under `examples/`.
- `pdks/` and `libs_common/` are shared infrastructure and should remain stable and reusable.
- Generated outputs for labs SHOULD go to `labs/<lab-id>/artifacts/` to keep labs self-contained.
- Task status MUST live only in GitHub Issue labels.
- Architect owns issue creation and planning; Executor/Reviewer update permitted issue labels and PR linkage.

## Verification protocol
- Context consistency:
  - `gh issue list --state open --label task:ready`
  - `gh issue list --state open --label task:in_progress`
- Smoke compile (per experiment task):
  - `asdlc netlist <entry.asdl> --backend <backend>`
- Simulation and analysis commands are task-specific and must be listed in each ExecPlan + issue validation section.

## Decision log
- 2026-03-01: Use `playground/agents` as canonical workflow authority for planning/execution/review.
- 2026-03-01: Promote shared infrastructure to repo root (`pdks/`, `libs_common/`).
- 2026-03-01: Standardize experiment authoring under root `libs/`, with one experiment per library directory.
- 2026-03-01: Remove archived historical example payload from active workspace to keep the playground focused.
