# Policies

Tier 1 durable knowledge. These are principles that remain valid independent of specific
bug states, tool versions, or codebase patches.

**Gating rule:** If the knowledge would become obsolete after a code fix, it belongs in
`agents/lessons/`, not here.

## Index

| ID | Content summary | Triggers |
|---|---|---|
| pol-79e52d7d | Theory-simulation correlation | analyze, lab-closeout, validate |
| pol-cd4eb5bf | Incremental modular construction | design, compile, author |
| pol-543a213e | Script-first analysis | analyze, plot, post-process |
| pol-27e721d2 | Deterministic validation first | validate, analyze |
| pol-49a45c2f | Sign conventions and formulas | analyze, plot, loop circuits |
| pol-57a7f401 | Observability-driven probing | design, simulate, analyze |
| pol-9ce3e7e4 | Experiment analysis recipe | lab-closeout, analyze |
| pol-0f9b64b9 | Close the loop on guidance | architect, reviewer |
| pol-4066ffcb | Repo hygiene | executor |
| pol-581cb230 | Compile-only sanity pass first | compile, simulate |
| pol-9d4b6cd7 | Simulator exit code is primary signal | simulate |
| pol-eb68439c | ASDL variable brace substitution | author, compile, design |
| pol-97e73c75 | Record scope approvals in PR comments | reviewer |
| pol-3709d324 | Rank telemetry failures by actionability | telemetry, architect |

## Usage

Architect queries at ExecPlan creation time:
```bash
python3 agents/scripts/query_lessons.py --phases compile --role executor
```

Reference policies in ExecPlan `Relevant Priors` section by ID.
