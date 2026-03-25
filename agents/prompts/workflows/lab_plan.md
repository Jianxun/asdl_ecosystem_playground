# Lab Plan Workflow Prompt

Use this prompt to generate `labs/plans/<lab-id>.md` from `labs/specs/<lab-id>.yaml`.

The lab plan format must follow `agents/prompts/workflows/execplan.md` **strictly**. Section structure is scaffolded by tooling.

## Purpose

- Translate a high-level lab spec into an executable plan.
- Keep implementation flexible while making validation and acceptance concrete.
- Produce a self-contained plan an executor can run without chat context.

## Inputs

Required:

- `labs/specs/<lab-id>.yaml`
- `agents/scripts/new_execplan.py`

Recommended:

- `agents/prompts/workflows/execplan.md`
- `agents/context/objectives.md`
- `agents/context/curriculum.md`
- `agents/instructions/packet-lab-workflow.md`

## Output

- One file: `labs/plans/<lab-id>.md`
- The plan must preserve the scaffolded section structure from `new_execplan.py`.

## Scaffold-first workflow

1. Generate scaffold with the helper:

   ```bash
   python3 agents/scripts/new_execplan.py --slug <lab-id> --title "Lab Plan: <Lab Title>"
   ```

2. Move scaffold to lab plans location:

   ```bash
   mv agents/plans/<lab-id>.md labs/plans/<lab-id>.md
   ```

3. Fill the scaffold using `labs/specs/<lab-id>.yaml` as source of truth.

4. Keep all scaffolded section headers unchanged (no additions/reordering/renaming).

## Lab-specific content mapping (within the fixed sections)

- `Purpose / Big Picture`: summarize the lab concept, learning goal, and key tradeoff from the spec.
- `Context and Orientation`: cite spec path (`labs/specs/<lab-id>.yaml`) and restate mechanisms/evidence expectations.
- `Plan of Work`: milestone-based execution strategy for author -> compile -> simulate -> normalize -> plot -> write-up.
- `Concrete Steps`: explicit, runnable steps from repo root with paths.
- `Validation and Acceptance`: map checks directly to spec mechanisms/tradeoffs/evidence; include at least one quantitative theory-vs-simulation threshold.
- `Idempotence and Recovery`: include restart-safe rerun path and failure triage for compile/simulate/normalize/plot issues.
- `Artifacts and Notes`: list planned outputs and locations.
- `Interfaces and Dependencies`: include simulator/backend assumptions, scripts, and relevant shared assets.

## Formatting and quality requirements

- Follow all formatting and reflection rules in `execplan.md` and the scaffold text.
- `Progress` must use checkboxes and timestamps.
- Validation must include commands and expected observations.
- Keep prose novice-readable and restartable.
- Avoid placeholders like `TBD` at handoff.

## Anti-patterns

- Editing section structure manually instead of using the helper scaffold first.
- Any section drift from scaffold/`execplan.md` (extra sections, renamed headers, reordered headers).
- Repeating spec text without actionable plan details.
- Missing quantitative acceptance criteria.
- Missing recovery guidance.
- Turning the plan into low-level code-edit micro-instructions.
