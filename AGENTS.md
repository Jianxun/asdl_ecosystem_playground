# AGENTS.md

Repository-level guidance for coding agents working in this project.

## Scope

- This repository is an ASDL playground focused on teaching-first lab development and workflow ergonomics.
- Prefer small, focused changes that improve reproducible lab loops.

## Source of Truth

Primary workflow authority lives under `agents/`.

Read in this order:

1. `agents/roles/<role>.md` (architect/executor/reviewer contract)
2. `agents/context/contract.md`
3. `agents/context/objectives.md`
4. `agents/context/curriculum.md`
5. `agents/context/github_issues_task_tracking.md`
6. `agents/prompts/workflows/execplan.md`
7. `agents/instructions/README.md`
8. Relevant instruction packets in `agents/instructions/packet-*.md`

## Normative Policies

- Task state source of truth is GitHub Issues + labels, not repo-local task YAML.
- Use `agents/scripts/new_execplan.py` to scaffold ExecPlans.
- Keep general task plans in `agents/plans/`; lab specs/plans/builds in `labs/specs/`, `labs/plans/`, `labs/builds/`.
- Keep generated lab artifacts in `labs/builds/<lab-id>/artifacts/`.
- Use explicit paths and run commands from repository root.
- Default backend is `sim.ngspice` unless explicitly testing alternatives.

## Expected Workflow

- Author a high-level lab spec in `labs/specs/<lab-id>.yaml` (what to demonstrate).
- Generate a plan scaffold with `agents/scripts/new_execplan.py`, then maintain the lab plan in `labs/plans/<lab-id>.md`.
- Implement and validate under `labs/builds/<lab-id>/` using compile -> simulate -> normalize -> plot.
- Record exact commands, evidence, and friction in the plan and lab write-up.
- If new recurring guidance emerges, update `agents/instructions/` or workflow prompts in the same change.

## Safety and Hygiene

- Do not delete or overwrite user-authored unrelated changes.
- Avoid destructive git operations unless explicitly requested.
- Do not commit generated artifacts unless explicitly asked.
