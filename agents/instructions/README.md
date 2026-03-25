# Agent Instructions — Hydration Packets

Modular context packets for agent sessions. Inject the relevant subset based on task type.

## Packets

| File | Purpose | Inject when |
|---|---|---|
| `packet-lab-workflow.md` | Normative lab execution policy and run loop | Starting any lab task |
| `packet-environment.md` | Environment verification and config pointers | New session or after env changes |
| `packet-debugging.md` | Failure triage for compile/simulate/post-process | Any failure occurs |
| `packet-tooling.md` | Tool reference and command syntax | Command lookup needed |
| `packet-snippets.md` | Copy-ready ASDL and command patterns | Authoring a new testbench |
| `packet-glossary.md` | Key term definitions | Clarification needed |

## Typical injection sets by role

- **Executor (lab task)**: `packet-lab-workflow` + `packet-environment` + `packet-snippets`
- **Executor (debugging)**: `packet-debugging` + `packet-tooling`
- **Architect (planning)**: `packet-lab-workflow` (for scope reference)
- **Reviewer**: none required by default

## Relationship to policies and lessons

Packets are operational guidance. For behavioral rules and experiential knowledge,
see `agents/policies/` and `agents/lessons/`.
