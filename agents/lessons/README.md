# Lessons

Tier 2 time-scoped knowledge. Each entry has an explicit `expires_when` condition.
Lessons are liabilities — they should pressure resolution of the underlying root cause.

**Gating rule:** Every entry must have a concrete `expires_when.condition` and a
`watch` file or issue. If no expiry condition can be stated, it belongs in `agents/policies/`.

## Index

| ID | Content summary | Expires when | Watch |
|---|---|---|---|
| les-200a5ad7 | sim.save_dc not valid; use sim.save sim_type | sim.save_dc defined in libs_common | libs_common/simulation.ngspice.asdl |
| les-8d13b924 | Xyce symbolic dc values unreliable; use literals | Xyce confirms symbolic values work | config/backends.yaml |
| les-32919b7e | Xyce save_op must emit DC in .PRINT | ASDL emitter handles this automatically | libs_common/simulation.xyce.asdl |
| les-1314fd5f | history.py global flags before subcommands | CLI refactored to accept flags anywhere | agents/tools/opencode_session_pipeline/bin/history.py |

## Garbage Collection

Run a GC session when:
- A significant library or tooling update lands
- A watched file changes
- A referenced issue closes

GC steps: scan entries → check watch files → archive/promote/keep.
