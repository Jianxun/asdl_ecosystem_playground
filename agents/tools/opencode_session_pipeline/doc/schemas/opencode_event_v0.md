# OpenCode Canonical Event Schema v0

This document defines the normalized event layer generated from raw ingestion records.

## Purpose

Provide a deterministic, auditable, query-friendly timeline that is:

- coarser than raw records
- rich enough for replay/postmortem/lesson extraction
- traceable back to raw provenance

## Granularity Policy (v0)

Emit a canonical event when there is a meaningful transition in:

- actor
- state
- decision checkpoint
- artifact impact
- failure/outcome signal

Do not emit part-level chatter that does not affect those transitions.

## Output Layout

- Per-session normalized events:
  - `archive/derived/events/opencode/<project_name>/session_<session_id>.events.jsonl`
- Per-session event manifest:
  - `archive/manifests/opencode/<project_name>/session_<session_id>.events.manifest.json`
- Event index:
  - `archive/index/opencode/<project_name>/events_index.jsonl`
  - `archive/index/opencode/<project_name>/events_index.manifest.json`
- Checkpoint:
  - `archive/checkpoints/opencode_events_state.json`

## Event Envelope

Each JSONL line is one canonical event.

```json
{
  "event_id": "evt_7d2f1a0e9b3c4d5e",
  "event_fingerprint": "<sha256 deterministic key>",
  "schema_version": "opencode_event_v0",
  "normalizer_version": "v0.1.0",
  "session_id": "ses_xxx",
  "project_label": "trail_blazer",
  "seq": 42,
  "event_type": "tool_execution",
  "event_time": 1739950060000,
  "record_time": "2026-03-13T01:23:45Z",
  "actor_role": "tool",
  "status": "completed",
  "severity": "info",
  "payload_compact": {},
  "provenance": {
    "source_table": "part",
    "row_id": "msg_xxx:part_yyy",
    "record_type": "part",
    "record_fingerprint": "<raw record fingerprint>",
    "source_payload_sha256": "<sha from raw>",
    "payload_sha256": "<sha from raw>",
    "time_created": 1739950059000,
    "time_updated": 1739950060000
  }
}
```

## Required Fields

- `event_id`
- `event_fingerprint`
- `schema_version`
- `normalizer_version`
- `session_id`
- `project_label`
- `seq`
- `event_type`
- `event_time`
- `record_time`
- `actor_role`
- `payload_compact`
- `provenance`

`status` and `severity` are optional but recommended.

## Event Type Taxonomy (v0)

- `session_started`
- `session_archived`
- `user_turn`
- `assistant_turn`
- `message_observed`
- `artifact_batch_changed`
- `tool_execution`
- `tool_failure`
- `validation_result`
- `todo_state_changed`

## Type-Specific Payload Guidelines

### `session_started`

- include: session title, directory, slug, version

### `session_archived`

- include: archive timestamp metadata (if present)

### `user_turn` / `assistant_turn`

- include: message id, parent id, model/provider metadata when available
- include small operational context, not full text body

### `artifact_batch_changed`

- include: diff count, list of affected files/status/additions/deletions (bounded)

### `tool_execution`

- include: tool name, call id, status, exit code, input/output hashes/lengths, timing

### `tool_failure`

- include: tool name, call id, status, exit code, output preview (if available)

### `validation_result`

- include: validator kind (heuristic), command preview/hash, pass/fail signal

### `todo_state_changed`

- include: position, content/title snapshot, status, priority
- emit only on state hash change per position

## Determinism and Idempotency

- `event_fingerprint` must be stable from deterministic fields.
- Recommended construction:
  - `sha256(session_id|event_type|event_time|record_fingerprint|payload_hash)`
- `seq` is assigned from deterministic event order in session snapshot.
- Full session event file can be regenerated deterministically from raw file.

## Provenance Rules

- Every canonical event MUST include a `provenance.record_fingerprint` pointer to raw.
- Canonical events may compact payloads but MUST preserve traceability back to raw rows.

## What Not to Encode in v0

- free-form interpretations without evidence
- lesson judgments
- policy decisions
- confidence scoring not directly grounded in objective evidence

Those belong in derived annotation/lesson layers.

## Evolution Notes

If postmortems repeatedly require details only visible in raw, promote those details into canonical payloads in v1.
If event volume grows with low utility, demote noisy fields/events back to raw-only.
