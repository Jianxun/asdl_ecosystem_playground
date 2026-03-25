# Packet: Tooling Reference

Reference for tools used in ASDL Playground labs.

**Inject when:** Needed for command syntax or tool capability lookup.

## Core toolchain

| Tool | Purpose | Invocation |
|---|---|---|
| `asdlc` | ASDL compiler | `asdlc netlist <entry.asdl> --backend sim.ngspice` |
| `ngspice` | Simulator | `ngspice -b -o <log> <netlist.spice>` |
| `normalize_raw.py` | RAW → HDF5 | `./venv/bin/python analysis/tools/ngspice/normalize_raw.py --input <tb.raw> --output <tb.hdf5>` |

## Workflow scripts

| Script | Purpose |
|---|---|
| `agents/scripts/task_dispatcher.py` | Launch executor/reviewer codex agents for GitHub issues |
| `agents/scripts/new_execplan.py` | Scaffold a new ExecPlan under `agents/plans/` |
| `agents/scripts/run_opencode_ingestion.sh` | One-command session ingest → normalize → validate |
| `agents/scripts/query_lessons.py` | Retrieve ranked policies/lessons by trigger match *(planned)* |

## Telemetry pipeline (`agents/tools/opencode_session_pipeline/`)

| Script | Purpose |
|---|---|
| `bin/ingest_raw.py` | Ingest raw OpenCode session logs to `archive/` |
| `bin/normalize_events.py` | Normalize raw events to canonical event schema |
| `bin/validate_events.py` | Validate normalized event files |
| `bin/history.py` | Query session telemetry (global flags must precede subcommands — see `les-1314fd5f`) |

## Command style conventions

- Run all commands from repo root.
- Use explicit input/output paths — no implicit working directory assumptions.
- Treat ngspice model-card warnings as non-fatal; check exit code (see `pol-9d4b6cd7`).
