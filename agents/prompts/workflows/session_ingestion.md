# Session Ingestion Workflow Prompt

This document defines the standard workflow for ingesting OpenCode session logs and producing canonical event timelines for harness analysis.

Use this prompt when you need to refresh session telemetry, validate archive integrity, or query event history for friction analysis.

## Purpose

The ingestion workflow creates durable, replayable telemetry artifacts that complement ExecPlans:

- Raw session archive (`jsonl`) for high-fidelity traces.
- Canonical events (`jsonl`) for deterministic downstream analytics.
- Validation reports for coverage and schema integrity.

## Canonical entrypoint (normative)

Always run ingestion through the repo wrapper script:

```bash
./agents/scripts/run_opencode_ingestion.sh
```

Optional mode override:

```bash
./agents/scripts/run_opencode_ingestion.sh incremental
./agents/scripts/run_opencode_ingestion.sh backfill
```

Do not manually stitch ingest/normalize/validate commands unless debugging the pipeline itself.

## Output locations (normative)

All ingestion outputs must live under repo-root `archive/`:

- `archive/raw/opencode/<project>/`
- `archive/derived/events/opencode/<project>/`
- `archive/manifests/opencode/<project>/`
- `archive/index/opencode/<project>/`
- `archive/checkpoints/`

`archive/` is operational data and must stay out of git.

## Required run sequence

The wrapper executes these stages in order:

1. **Raw ingest**
   - Source: OpenCode SQLite DB
   - Output: raw session JSONL + manifests + session index
2. **Event normalization**
   - Input: raw archive
   - Output: canonical events JSONL + manifests + events index
3. **Validation**
   - Checks raw/event coverage and event integrity
   - Output: `events_validation.json`

## Acceptance criteria

An ingestion run is complete only when all are true:

- Wrapper exits with code `0`.
- `archive/index/opencode/<project>/sessions_index.jsonl` exists.
- `archive/index/opencode/<project>/events_index.jsonl` exists.
- `archive/index/opencode/<project>/events_validation.json` exists.
- Validation summary reports:
  - `failed=0`
  - `missing_events=0`
  - `missing_raw=0`

## Troubleshooting conventions

- If validation fails due to project scoping mismatch, confirm the wrapper is run from repo root and not from inside the pipeline packet directory.
- If archive paths are missing, confirm `archive/` exists at repo root and that local permissions allow writes.
- If no sessions are found, treat as informational unless recent sessions are expected; record this as a telemetry gap.

## Querying event history

Use history queries after a successful ingestion run:

```bash
python3 agents/tools/opencode_session_pipeline/bin/history.py --project <project> timeline --session-id <session_id>
python3 agents/tools/opencode_session_pipeline/bin/history.py --project <project> tools --session-id <session_id> --failed-only
```

Global flags must be placed before subcommands.

## Distillation expectations

After ingestion, downstream analysis should extract structured friction signals (for example retries, high tool usage, long chained commands) and connect them to task/lab outcomes before proposing harness changes.

## Safety and hygiene

- Treat archive data as append-only operational telemetry.
- Do not edit generated archive files by hand.
- Keep schema/pipeline code under version control; keep archive payloads out of git.
