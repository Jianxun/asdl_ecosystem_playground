# Contract

## Project overview
ASDL Playground is an experimentation repository for exercising the ASDL authoring-to-simulation workflow end to end. The primary goal is to stress test language semantics, compiler/emission behavior, simulator integration, and result analysis workflows while producing reusable guidance for future agents.

The repository is intentionally split between infrastructure (`pdks/`, `libs_common/`, backend config) and experiment libraries (`libs/`). The `agents/` workflow is the canonical operating model for planning, execution, review, and context continuity.

## System boundaries / components
- `agents/`: canonical agent workflow (roles, context, scripts, scratchpads, logs).
- `libs/`: experiment libraries; one experiment per subdirectory.
- `libs_common/`: shared reusable ASDL blocks (for example sources and simulation directives).
- `pdks/`: PDK wrappers and simulator model assets used by experiments.
- `examples/`: legacy/reference assets (config/docs/scratch), not the primary authoring location.
- `analysis/`: post-processing scripts and metric extraction.
- `docs/`: experiment reports and playbooks.
- `runs/`: generated outputs (netlists/logs/waveforms/metrics), git-ignored.

## Interfaces & data contracts
- Project config is driven by repo-root `.asdlrc`.
- `.asdlrc` sets:
  - `backend_config: ${ASDLRC_DIR}/config/backends.yaml`
  - `lib_roots`: `${ASDLRC_DIR}/pdks/${PDK}/asdl`, `${ASDLRC_DIR}/libs_common`, `${ASDLRC_DIR}/libs`
  - `env` variables for `PDK`, `PDK_PATH`, `PDK_ASDL_PATH`, `ASDL_DESIGN_LIBS_PATH`, and `ASDL_LIB_PATH`.
- Task planning and status contracts:
  - `agents/context/tasks.yaml` is the task card source of truth (`schema_version: 2`).
  - `agents/context/tasks_state.yaml` is the task runtime state map (`schema_version: 2`).
  - `agents/context/tasks_icebox.yaml` and `agents/context/tasks_archived.yaml` use `schema_version: 1`.

## Invariants
- `agents/` workflow is canonical for project execution and handoff.
- New experiment source lives in `libs/`; do not create new canonical experiment source under `examples/`.
- `pdks/` and `libs_common/` are shared infrastructure and should remain stable and reusable.
- Generated outputs MUST go to `runs/` (or other explicitly generated paths), not under `libs/`.
- Task status MUST live only in `agents/context/tasks_state.yaml`.
- Architect owns task cards and project status; Executor/Reviewer only update permitted state fields.

## Verification protocol
- Context consistency:
  - `./venv/bin/python agents/scripts/lint_tasks_state.py`
- Smoke compile (per experiment task):
  - `asdlc netlist <entry.asdl> --backend <backend>`
- Simulation and analysis commands are task-specific and must be listed in each task `verify` block.

## Decision log
- 2026-03-01: Use `playground/agents` as canonical workflow authority for planning/execution/review.
- 2026-03-01: Promote shared infrastructure to repo root (`pdks/`, `libs_common/`).
- 2026-03-01: Standardize experiment authoring under root `libs/`, with one experiment per library directory.
- 2026-03-01: Remove archived historical example payload from active workspace to keep the playground focused.
