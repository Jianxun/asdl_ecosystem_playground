# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- Canonical workflow authority is `playground/agents` with Architect/Executor/Reviewer role files active.
- Project direction is now lab-first curriculum development under `labs/`.
- Default lab backend policy is `sim.ngspice`; labs normalize RAW -> HDF5 and plot from HDF5.
- OpenCode session ingestion pipeline is active with repo-root archive at `archive/`.
- Canonical ingestion entrypoint is `./agents/scripts/run_opencode_ingestion.sh`.
- Session ingestion workflow prompt is available at `agents/prompts/workflows/session_ingestion.md`.
- Lab-01 delivery exists and is in review state (`T-016`, PR `#4`).

## Last verified status
- `./venv/bin/python agents/scripts/lint_tasks_state.py` (passes on consolidated `tasks.yaml`)
- `./agents/scripts/run_opencode_ingestion.sh incremental` (ingest -> normalize -> validate passes)

## Next steps (1-3)
1. Tune event normalization heuristics for actionable friction extraction (command complexity, phase tags, failure actionability).
2. Re-run ingestion after heuristic updates and compare signal quality on `ses_2dd8afe3dffeznX4Gcqb8Fi723`.
3. Convert repeated telemetry patterns into durable harness guidance/prompts.

## Risks / unknowns
- Heuristic changes may overfit one session if not validated across multiple lab/executor sessions.
- Raw session logs contain noisy events; without actionability scoring, false-positive friction signals can dominate.
- Prompt/workflow churn may outpace evidence unless promotion thresholds are explicit.

## Session handoff
- Latest handoff note: `agents/context/handoff_2026-03-25.md`
