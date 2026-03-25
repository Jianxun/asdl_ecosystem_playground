# Improve Session Event Heuristics

## Purpose / Big Picture

Improve OpenCode event normalization so session-derived telemetry is more actionable for harness evolution. Use lab-01 executor session `ses_2dd8afe3dffeznX4Gcqb8Fi723` as the seed case, then verify that heuristic upgrades remain deterministic and useful across all available `playground` sessions.

## Progress

- [x] 2026-03-25 00:00Z Task seeded with baseline findings and handoff context.
- [x] 2026-03-25 09:45Z Architect refreshed context (`objectives.md`, `curriculum.md`) and upgraded this ExecPlan to execution-ready detail.
- [x] 2026-03-25 04:28Z Implemented deterministic command/failure heuristics in normalizer and documented payload contract updates.
- [x] 2026-03-25 04:29Z Re-normalized via backfill (after incremental no-op on unchanged sessions), validated project-wide coverage, and compared baseline vs post-update metrics for target session.
- [x] 2026-03-25 04:30Z Distilled promotion outcome: keep heuristic logic in pipeline + schema docs for now; defer prompt/instruction promotion until repeated multi-session evidence accumulates.

## Surprises & Discoveries

- Baseline events already preserve deterministic provenance, so heuristics should be additive in payloads before introducing taxonomy changes.
- `validate_events.py` enforces a fixed event-type allowlist; adding new event kinds would require validator/schema updates and increases rollout risk.
- High-value friction is currently present in existing fields (`command_preview`, `output_preview`) but not promoted into structured dimensions.
- Incremental mode only re-normalizes changed raw session files; code-only heuristic changes required a `backfill` run to regenerate existing session event outputs.

## Decision Log

- Decision: Start with additive heuristics (new fields/tags) before changing existing event contracts.
  - Rationale: Preserve backward compatibility for existing event consumers.
- Decision: Keep `event_type` taxonomy unchanged in this task and enrich `tool_execution` / `tool_failure` payloads instead.
  - Rationale: Validator and downstream tools already depend on v0 taxonomy; payload enrichment gives immediate signal gains with low migration cost.
- Decision: Implement deterministic failure signatures with simple pattern mapping for known simulator/tool errors.
  - Rationale: Signature stability is needed for trend tracking and promotion thresholds.
- Decision: Gate promotion to instructions/prompts on repeated evidence, not single-session anecdotes.
  - Rationale: Avoid overfitting harness behavior to one noisy run.

## Outcomes & Retrospective

Outcome achieved: event streams now include deterministic command-complexity + command-phase heuristics and failure actionability/signature metadata while preserving the v0 taxonomy and core event counts for the seed session.

## Context and Orientation

Primary files:

- `agents/tools/opencode_session_pipeline/bin/normalize_events.py`
- `agents/tools/opencode_session_pipeline/bin/validate_events.py`
- `agents/tools/opencode_session_pipeline/doc/schemas/opencode_event_v0.md`
- `archive/derived/events/opencode/playground/session_ses_2dd8afe3dffeznX4Gcqb8Fi723.events.jsonl`
- `agents/context/handoff_2026-03-25.md`

Working assumptions:

- Commands run from repository root.
- Ingestion is executed via `./agents/scripts/run_opencode_ingestion.sh`.
- Archive files under `archive/` are generated artifacts; pipeline code/docs are versioned.

## Plan of Work

1. Baseline and contract check.
   - Re-run ingestion and capture baseline metrics for target session and project-level validation.
   - Confirm current schema/validator constraints before editing heuristics.
2. Deterministic heuristic design.
   - Add command complexity fields (`command_len`, `chain_count`, `has_heredoc`).
   - Add command phase classification (`compile`, `simulate`, `normalize`, `plot`, `git`, `pr`, `meta`, fallback `unknown`).
   - Add failure actionability and failure signature fields for `tool_failure`.
3. Implementation and documentation.
   - Implement deterministic extraction in `normalize_events.py`.
   - Document new payload fields in `opencode_event_v0.md` (type-specific payload guidance).
4. Re-normalize and evaluate.
   - Re-run ingestion/validation and compare pre/post distributions.
   - Confirm reduced low-value failure noise and preserved core counts.
5. Distill and handoff.
   - Update relevant instruction/prompt files only if evidence supports promotion.
   - Prepare PR with evidence table and explicit follow-up thresholds.

## Concrete Steps

1. Set execution state and branch.
   - Update `T-017` status to `in_progress` in `agents/context/tasks.yaml`.
   - Run: `./venv/bin/python agents/scripts/lint_tasks_state.py`
   - Create branch from `main` (example): `git checkout -b feat/t-017-event-heuristics`
2. Capture baseline evidence (before edits).
   - Run: `./agents/scripts/run_opencode_ingestion.sh incremental`
   - Run: `python3 agents/tools/opencode_session_pipeline/bin/history.py --project playground tools --session-id ses_2dd8afe3dffeznX4Gcqb8Fi723 --failed-only`
   - Record key baseline metrics from:
     - `archive/manifests/opencode/playground/session_ses_2dd8afe3dffeznX4Gcqb8Fi723.events.manifest.json`
     - `archive/index/opencode/playground/events_validation.json`
3. Implement heuristic extraction in `normalize_events.py`.
   - Add deterministic command analysis helpers.
   - Enrich `tool_execution.payload_compact.input` and/or sibling payload keys with complexity and phase fields.
   - Enrich `tool_failure.payload_compact` with:
     - `failure_actionability` (`high`, `medium`, `low`)
     - `failure_signature` (stable string key)
     - optional `failure_family` (for grouped reporting)
4. Update schema docs for payload additions.
   - Edit: `agents/tools/opencode_session_pipeline/doc/schemas/opencode_event_v0.md`
   - Keep event taxonomy unchanged in this task.
5. Re-run normalization and validate.
   - Run: `./agents/scripts/run_opencode_ingestion.sh incremental`
   - Run: `python3 agents/tools/opencode_session_pipeline/bin/validate_events.py --project playground --raw-root archive/raw/opencode --events-root archive/derived/events/opencode --index-root archive/index`
6. Produce pre/post comparison evidence.
   - Compare baseline vs updated manifest counts for target session.
   - Show at least one failure previously treated as generic now carrying a deterministic signature and actionability classification.
   - Confirm core event counts remain stable (`tool_execution`, `tool_failure`, turns).
7. Close out for review.
   - Commit changes, push branch, open PR to `main`.
   - Update `T-017` to `ready_for_review` with `pr` number and `merged: false`, then rerun `./venv/bin/python agents/scripts/lint_tasks_state.py`.
   - Record PR URL and evidence links in this ExecPlan.

## Validation and Acceptance

Acceptance requires:

- Wrapper run succeeds: `./agents/scripts/run_opencode_ingestion.sh incremental` exits `0`.
- Validation succeeds with no coverage gaps:
  - `archive/index/opencode/playground/events_validation.json` reports `failed=0`, `missing_events=0`, `missing_raw=0`.
- Target session event payloads include new deterministic fields:
  - command complexity + phase in `tool_execution`
  - actionability + signature in `tool_failure`
- At least one previously low-actionability failure is explicitly labeled `low` with rationale encoded by deterministic signature mapping.
- No regression in core counts for target session: `session_started`, `tool_execution`, `tool_failure`, `assistant_turn`, `user_turn`.
- Git closeout complete and recorded:
  - feature branch exists,
  - validation evidence captured in plan,
  - branch pushed,
  - PR open to `main`,
  - PR URL present in this file.

## Idempotence and Recovery

- Pipeline is file-backed and checkpointed; reruns are expected.
- If incremental mode does not pick up code-only heuristic changes, rerun with backfill:
  - `./agents/scripts/run_opencode_ingestion.sh backfill`
- If output contract breaks, revert heuristic patch, rerun wrapper, and confirm validation recovers.
- If signature patterns overfit one session, keep mapping minimal and move broadening logic to a follow-up task.

## Artifacts and Notes

- Event manifests and index under `archive/index/opencode/playground/`.
- Handoff and findings in `agents/context/handoff_2026-03-25.md`.
- Baseline target-session manifest (pre-change):
  - `event_count=157`, `tool_execution=90`, `tool_failure=3`, `assistant_turn=61`, `user_turn=1`
  - source: `archive/manifests/opencode/playground/session_ses_2dd8afe3dffeznX4Gcqb8Fi723.events.manifest.json` before heuristic patch
- Post-change target-session manifest (after backfill):
  - `event_count=157`, `tool_execution=90`, `tool_failure=3`, `assistant_turn=61`, `user_turn=1`, `normalizer_version=v0.2.0`
  - source: `archive/manifests/opencode/playground/session_ses_2dd8afe3dffeznX4Gcqb8Fi723.events.manifest.json`
- Deterministic failure enrichment examples:
  - Xyce failure tagged `failure_signature=xyce.analysis_print_type_mismatch`, `failure_actionability=high`, `failure_family=simulate`
  - Read-tool noise failures tagged `failure_signature=tool.read.null_output_error`, `failure_actionability=low`, `failure_family=tool_io`
  - source: `archive/derived/events/opencode/playground/session_ses_2dd8afe3dffeznX4Gcqb8Fi723.events.jsonl`
- Command heuristic enrichment examples:
  - compile chain: `chain_count=4`, `command_phase=compile`
  - PR heredoc command: `has_heredoc=true`, `command_phase=pr`
  - source: `archive/derived/events/opencode/playground/session_ses_2dd8afe3dffeznX4Gcqb8Fi723.events.jsonl`
- Validation evidence:
  - `./agents/scripts/run_opencode_ingestion.sh incremental` succeeded (`checked=13 ok=13 failed=0 missing_events=0 missing_raw=0`)
  - `./agents/scripts/run_opencode_ingestion.sh backfill` succeeded (`checked=13 ok=13 failed=0 missing_events=0 missing_raw=0`)
  - `python3 agents/tools/opencode_session_pipeline/bin/validate_events.py --project playground --raw-root archive/raw/opencode --events-root archive/derived/events/opencode --index-root archive/index` succeeded
  - report: `archive/index/opencode/playground/events_validation.json`
- PR URL: TBD (executor fills at review-ready handoff).

## Interfaces and Dependencies

- `ingest_raw.py`, `normalize_events.py`, `validate_events.py`, `history.py`
- Wrapper script: `agents/scripts/run_opencode_ingestion.sh`
- Task state linter: `agents/scripts/lint_tasks_state.py`

## Final Reflection Round

### Outcome
- Implemented additive deterministic event heuristics for command complexity/phase and tool-failure actionability/signatures without changing event taxonomy.
- Re-normalization + validation passed across all available `playground` sessions, and target-session core counts remained stable.

### What Changed
- Updated `agents/tools/opencode_session_pipeline/bin/normalize_events.py`:
  - bumped `normalizer_version` to `v0.2.0`
  - added command helpers (`chain_count`, heredoc detection, phase classifier)
  - enriched `tool_execution.payload_compact.input` with `chain_count`, `has_heredoc`, `command_phase`, and deterministic `command_len` fallback
  - enriched `tool_failure.payload_compact` with `failure_signature`, `failure_actionability`, `failure_family`, and `command_phase`
- Updated `agents/tools/opencode_session_pipeline/doc/schemas/opencode_event_v0.md` with the new payload guidance for `tool_execution` and `tool_failure`.
- Updated task execution state in `agents/context/tasks.yaml` (`T-017` moved to `in_progress` during execution).

### Key Decisions and Trade-offs
- Kept taxonomy unchanged and focused on additive payload enrichment to avoid validator/downstream migration cost.
- Used simple deterministic pattern mapping for failure signatures to maximize stability; accepted lower immediate recall for unknown failure families.
- Kept prompt/instruction promotion deferred because this run demonstrates viability but not yet repeated cross-session trend thresholds.

### Lessons Learned
- Code-only normalizer edits require `backfill` to refresh historical event files because incremental mode keys off raw file hashes.
- Deterministic failure tags materially improve triage without increasing event volume.
- Command-phase heuristics are useful even when command outputs are absent, but classification quality depends on hint coverage and should be expanded cautiously.

### Memories to Promote
- Prefer additive payload fields before event taxonomy changes when validators enforce strict allowlists.
- Include a low-actionability signature bucket for tool noise to prevent over-weighting non-actionable failures.

### Frictions and Complaints
- `history.py` remains event-type oriented and does not yet summarize new failure-signature distributions directly; manual inspection was needed.

### Improvement Proposals
- Add a small `history.py` mode (or flag) to aggregate `failure_signature` and `failure_actionability` counts by session.
- Add deterministic phase-hint tests for ambiguous command previews to avoid regression in classifier behavior.
- Define promotion thresholds (e.g., repeated signature frequency across >=3 sessions) before instruction/prompt edits.

### Evidence
- Baseline command: `./agents/scripts/run_opencode_ingestion.sh incremental`
- Baseline failures command: `python3 agents/tools/opencode_session_pipeline/bin/history.py --project playground tools --session-id ses_2dd8afe3dffeznX4Gcqb8Fi723 --failed-only`
- Post-change commands:
  - `./agents/scripts/run_opencode_ingestion.sh incremental`
  - `./agents/scripts/run_opencode_ingestion.sh backfill`
  - `python3 agents/tools/opencode_session_pipeline/bin/validate_events.py --project playground --raw-root archive/raw/opencode --events-root archive/derived/events/opencode --index-root archive/index`
- Artifacts:
  - `archive/manifests/opencode/playground/session_ses_2dd8afe3dffeznX4Gcqb8Fi723.events.manifest.json`
  - `archive/derived/events/opencode/playground/session_ses_2dd8afe3dffeznX4Gcqb8Fi723.events.jsonl`
  - `archive/index/opencode/playground/events_validation.json`

### Next Steps
- Open PR, then monitor reviewer feedback for additional signature mappings worth promoting in a follow-up task.

---

Revision note (2026-03-25): Expanded this plan from seed outline to an execution-ready workflow with explicit commands, acceptance gates, idempotence/recovery paths, and PR closeout requirements aligned to current telemetry objectives.
Revision note (2026-03-25 executor): Recorded implementation results, validation evidence, baseline/post comparisons, and completed final reflection based on backfill-regenerated event outputs.
