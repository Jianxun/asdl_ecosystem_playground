# Lab Spec Workflow Prompt

Use this prompt to generate `labs/specs/<lab-id>.yaml` as a high-level directive for a lab.

The lab spec defines **what the lab must teach and demonstrate**, not a step-by-step implementation recipe.

## Purpose

- Keep the lab intent stable while plans/builds can be regenerated.
- Encode concept, mechanisms, tradeoffs, and evidence expectations.
- Avoid handholding details that belong in ExecPlans or executor implementation.

## Spec philosophy

Write specs as constraints and outcomes:

- Include: learning intent, circuit behavior to demonstrate, expected evidence shape.
- Include: implementation-mode constraints that are stable policy (for example ASDL-first authoring).
- Exclude: exact commands, fixed filenames checklist, fixed parameter values, tool-by-tool steps.
- Keep language novice-readable and concrete enough to review.

## Authoring process

1. Choose one core concept and one primary tradeoff/property.
2. State why the circuit matters in practical terms.
3. List the mechanisms/behaviors that must be shown.
4. Define evidence expectations (theory-first + simulation + quantitative check).
5. Define delivery expectations at policy level (reproducible, follows repo conventions).
6. Save as `labs/specs/<lab-id>.yaml`.

## Required fields (minimum)

- `lab_id`
- `title`
- `difficulty`
- `directive` (concept, learning goal, practical context)
- `mechanisms_to_demonstrate` (list)
- `tradeoffs_to_explain` (list)
- `evidence_expectations` (list)
- `delivery_expectations` (list)

## Recommended structure

```yaml
lab_id: lab-XX-<slug>
title: "<human title>"
difficulty: beginner|intermediate|advanced

directive:
  concept: "<single core concept>"
  learning_goal: "<what the learner should understand after the lab>"
  practical_context: "<where this matters in real circuits>"

mechanisms_to_demonstrate:
  - "<behavior 1>"
  - "<behavior 2>"

tradeoffs_to_explain:
  - "<tradeoff 1>"

evidence_expectations:
  - "Theory-first explanation before simulation interpretation"
  - "Frequency and/or time-domain evidence appropriate to the concept"
  - "At least one quantitative theory-vs-simulation check with explicit tolerance"

delivery_expectations:
  - "Primary authoring uses ASDL sources; raw simulator netlists are generated artifacts"
  - "Reproducible from repo root with explicit paths"
  - "Generated outputs and figures follow project conventions"
```

## Quality gate

A spec is acceptable when all are true:

- It is high-level and directive, not procedural.
- It captures one concept and one key property/tradeoff clearly.
- It requires measurable evidence without prescribing implementation internals.
- It is understandable without chat/session context.

## Anti-patterns

- Embedding exact run commands in spec.
- Locking implementation to specific file names beyond necessary identity/path.
- Leaving authoring mode ambiguous when policy requires a specific source of truth (for example ASDL-first).
- Overconstraining device values unless essential to the learning objective.
- Turning spec into an ExecPlan.
