# Improve Session Event Heuristics

## Purpose / Big Picture

Improve OpenCode event normalization so session-derived telemetry is more actionable for harness evolution. Use lab-01 executor session `ses_2dd8afe3dffeznX4Gcqb8Fi723` as the seed case, then verify that heuristic upgrades remain deterministic and useful across all available `playground` sessions.

## Progress

- [x] 2026-03-25 00:00Z Task seeded with baseline findings and handoff context.
- [x] 2026-03-25 09:45Z Architect refreshed context (`objectives.md`, `curriculum.md`) and upgraded this ExecPlan to execution-ready detail.
- [ ] Implement and validate normalization updates.
- [ ] Re-ingest/re-normalize and compare pre/post signal quality.
- [ ] Distill accepted patterns into prompts/instructions.

## Surprises & Discoveries

- Baseline events already preserve deterministic provenance, so heuristics should be additive in payloads before introducing taxonomy changes.
- `validate_events.py` enforces a fixed event-type allowlist; adding new event kinds would require validator/schema updates and increases rollout risk.
- High-value friction is currently present in existing fields (`command_preview`, `output_preview`) but not promoted into structured dimensions.

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

Planned outcome: event streams that separate high-signal friction from low-signal noise and support reliable promotion decisions. Executor deliverable is a review-ready PR that updates the normalizer, schema docs, and execution guidance with evidence-backed thresholds.

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
- PR URL: TBD (executor fills at review-ready handoff).

## Interfaces and Dependencies

- `ingest_raw.py`, `normalize_events.py`, `validate_events.py`, `history.py`
- Wrapper script: `agents/scripts/run_opencode_ingestion.sh`
- Task state linter: `agents/scripts/lint_tasks_state.py`

## Final Reflection Round

### Outcome
- TBD

### What Changed
- TBD

### Key Decisions and Trade-offs
- TBD

### Lessons Learned
- TBD

### Memories to Promote
- TBD

### Frictions and Complaints
- TBD

### Improvement Proposals
- TBD

### Evidence
- TBD

### Next Steps
- TBD

---

Revision note (2026-03-25): Expanded this plan from seed outline to an execution-ready workflow with explicit commands, acceptance gates, idempotence/recovery paths, and PR closeout requirements aligned to current telemetry objectives.
