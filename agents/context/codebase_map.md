# Codebase Map

## Directories

### Agent workflow
- `agents/roles/`: Architect, Executor, Reviewer role contracts.
- `agents/context/`: project working memory — status, objectives, curriculum, system design, contract, handoffs.
- `agents/plans/`: active ExecPlan documents (one per task).
- `agents/scripts/`: workflow automation scripts (dispatcher, ingestion, lesson query).

### Knowledge store
- `agents/policies/`: Tier 1 durable policies (YAML). Permanent behavioral rules; not invalidated by code fixes.
- `agents/lessons/`: Tier 2 time-scoped lessons (YAML). Each has `expires_when` condition.
- `agents/episodes/`: Injection + outcome track records (JSONL, append-only).

### Instruction packets
- `agents/instructions/`: modular hydration packets injected into agent context by task type.

### Workflow prompts and skills
- `agents/prompts/workflows/`: structured workflow prompts (ExecPlan, lab, session ingestion).
- `agents/prompts/skills/`: task-oriented playbooks composing policies into concrete steps.

### Tooling
- `agents/tools/opencode_session_pipeline/`: OpenCode session ingest → normalize → validate → query pipeline.

### Lab pipeline
- `labs/specs/`: stable lab specs (YAML, never regenerated) — one file per lab.
- `labs/plans/`: architect-generated lab ExecPlans (regenerable from spec).
- `labs/builds/<lab-id>/`: executor-generated lab implementations (regenerable from plan).
- `labs/builds/<lab-id>/artifacts/`: generated simulation outputs (git-ignored by extension).

### Circuit infrastructure
- `libs_common/`: shared ASDL sources for common primitives and simulation helpers.
- `pdks/`: PDK models and ASDL wrappers.
- `examples/`: legacy/reference assets (not the primary authoring location).
- `analysis/`: post-processing scripts and metric extraction.
- `analysis/tools/ngspice/`: canonical ngspice RAW normalization tools.

### Telemetry archive
- `archive/`: repo-root telemetry archive for OpenCode session raw logs, canonical events, indexes, and checkpoints.

## Quick Reference: Workflow
- `agents/roles/architect.md`: project planning and issue authority.
- `agents/roles/executor.md`: task execution protocol.
- `agents/roles/reviewer.md`: review and merge closeout protocol.
- `agents/context/github_issues_task_tracking.md`: canonical issue label/state workflow.
- `agents/context/system_design.md`: evolving harness system design (self-improvement loop, knowledge store, build sequence).
- `agents/context/lab_pipeline_evaluation.md`: evaluation framework for spec → plan → implementation pipeline; defines stable artifacts, metrics, and improvement attribution.
- `agents/scripts/new_execplan.py`: creates an ExecPlan scaffold under `agents/plans/`.
- `agents/scripts/run_opencode_ingestion.sh`: one-command session ingest → normalize → validate.

## Quick Reference: Knowledge Store
- `agents/policies/README.md`: index of all active policies with trigger summary.
- `agents/lessons/README.md`: index of all active lessons with expiry conditions.
- `agents/episodes/README.md`: episode record format reference.

## Quick Reference: Instructions
- `agents/instructions/README.md`: packet index with injection guidance by role.

## Quick Reference: Configuration
- `.asdlrc`: project-level backend config, lib roots, env wiring.
- `config/backends.yaml`: backend template definitions.

## Quick Reference: Shared Libraries
- `libs_common/analoglib.asdl`: common analog source and passive device definitions.
- `libs_common/simulation.ngspice.asdl`: ngspice simulation directive definitions.

## Quick Reference: PDK Assets
- `pdks/gf180mcu/asdl/`: ASDL-facing PDK library entrypoints.
- `pdks/gf180mcu/ngspice/`: ngspice model and include assets.
- `pdks/gf180mcu/xyce/`: xyce model and include assets.
