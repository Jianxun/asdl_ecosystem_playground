# AGENTS.md

Repository-level guidance for coding agents working in this project.

## Scope

- This repository is an ASDL playground focused on authoring/tooling ergonomics.
- Prefer small, focused changes that support experiment loops.

## Source of Truth

Primary instructions live under `agents/instructions/`.

Read in this order:

1. `agents/instructions/playbook.md`
2. `agents/instructions/workflow.md`
3. `agents/instructions/quickstart.md`
4. `agents/instructions/debugging.md`
5. `agents/instructions/snippets.md`
6. `agents/instructions/tooling.md`
7. `agents/instructions/experiment_template.md`
8. `agents/instructions/glossary.md`

## Normative Policies

- Treat `agents/instructions/playbook.md` as normative execution policy.
- Keep source assets in `libs/<experiment_name>/`.
- Keep generated outputs in `runs/<experiment_name>/<run_id>/`.
- Use explicit paths and run commands from repository root.
- Default backend is `sim.xyce` unless explicitly testing alternatives.

## Expected Workflow

- Author minimal ASDL needed to answer one experiment question.
- Compile with `asdlc`, run with `xyce`, normalize with canonical analysis tools.
- Record exact commands, artifacts, friction points, and fixes in `docs/`.
- If new guidance emerges, update `agents/instructions/` in the same change.

## Safety and Hygiene

- Do not delete or overwrite user-authored unrelated changes.
- Avoid destructive git operations unless explicitly requested.
- Do not commit generated run artifacts unless asked.
