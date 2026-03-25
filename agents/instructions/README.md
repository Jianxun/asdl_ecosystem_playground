# Agent Instructions

These files are the hydration pack for agents working in ASDL Playground.

## Read order

1. `playbook.md` (normative execution policy)
2. `workflow.md` (experiment lifecycle and scope control)
3. `quickstart.md` (fast environment + run checklist)
4. `debugging.md` (failure triage)
5. `snippets.md` (copy-ready examples)
6. `tooling.md` (tool reference)
7. `experiment_template.md` (report schema)
8. `glossary.md` (terms)

## What is normative vs reference

- Normative policy: `playbook.md`, `workflow.md`
- Operational guidance: `quickstart.md`, `debugging.md`
- Reference material: `snippets.md`, `tooling.md`, `experiment_template.md`, `glossary.md`

## Purpose

- Keep agent behavior consistent across sessions.
- Reduce startup friction for ASDL author -> compile -> simulate -> analyze loops.
- Capture ergonomics findings that inform next-generation orchestration (separate from legacy `asdl_ecosystem/simorc`).

## Related workflow prompts

- Session ingestion workflow: `agents/prompts/workflows/session_ingestion.md`
