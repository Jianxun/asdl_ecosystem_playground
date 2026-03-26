# OpenCode Raw Ingestion Schema v0

This document backfills the schema produced by `tools/opencode/ingest_raw.py`.
It describes the on-disk raw archive contract under `archive/raw/opencode/<project>/`.

## Status

- Version: `v0.1.0` (matches `INGEST_VERSION` in `tools/opencode/ingest_raw.py`)
- Layer: raw archival ingestion
- Purpose: project-scoped, append-only, idempotent archival records with provenance

## Output Layout

- Per-session raw records:
  - `archive/raw/opencode/<project_name>/session_<session_id>.jsonl`
- Per-session manifest:
  - `archive/manifests/opencode/<project_name>/session_<session_id>.manifest.json`
- Session navigation index:
  - `archive/index/opencode/<project_name>/sessions_index.jsonl`
  - `archive/index/opencode/<project_name>/sessions_index.manifest.json`
- Incremental checkpoint:
  - `archive/checkpoints/opencode_ingest_state.json`

## Raw Record Envelope (JSONL row)

Each line in `session_<id>.jsonl` is one raw envelope record.

```json
{
  "record_type": "session|message|part|todo",
  "source_table": "session|message|part|todo",
  "row_id": "<source row id>",
  "project_id": "<opencode project id>",
  "session_id": "<session id>",
  "time_created": 1739950000000,
  "time_updated": 1739950060000,
  "ingested_at": "2026-03-13T01:23:45Z",
  "source_db_path": "/Users/<user>/.local/share/opencode/opencode.db",
  "payload_raw": {},
  "payload_sha256": "<sha256 of sanitized payload>",
  "source_payload_sha256": "<sha256 before sanitization>",
  "record_fingerprint": "<sha256(source_table|row_id|time_updated|source_payload_sha256)>",
  "payload_redaction": {
    "type": "message_data_compaction|tool_part_compaction|reasoning_encrypted_content",
    "bytes_removed": 12345
  },
  "ingest_version": "v0.1.0"
}
```

## Field Notes

- `record_fingerprint` is the idempotency key.
- `payload_raw` is source-like but can be compacted/redacted.
- `payload_sha256` reflects the sanitized payload stored in archive.
- `source_payload_sha256` preserves hash of the original payload before compaction/redaction.
- `payload_redaction` is optional (`null` when no compaction/redaction happened).

## Record-Type Specific Notes

### `session`

- `row_id` is `session.id`.
- `payload_raw` mirrors selected columns from OpenCode `session` row.

### `message`

- `row_id` is `message.id`.
- `payload_raw.data` is a compacted JSON string when parseable.
- Compaction keeps high-value metadata and bounded diff summary stats.

### `part`

- `row_id` is `part.id`.
- `payload_raw.data` is:
  - compacted for `type=tool` (hashes/lengths/status + bounded previews)
  - redacted for reasoning encrypted blob (`metadata.openai.reasoningEncryptedContent` removed)

### `todo`

- `row_id` is synthetic: `<session_id>:<position>`.
- `payload_raw` contains current todo row projection from source table.

## Ordering and Idempotency Guarantees

- Per-session file records are deterministically sorted by:
  1. `time_created`
  2. `source_table`
  3. `row_id`
  4. `time_updated`
  5. `record_fingerprint`
- Re-running ingestion does not duplicate records with the same `record_fingerprint`.
- Existing session files are appended only with newly observed fingerprints.

## Compaction/Redaction Contract

Compaction is intentional and transparent:

- `message.data` compaction
  - keep: role/time/parent/model/provider/mode/agent/path/variant/model
  - keep bounded diff summaries (`summary.diffs` compact projection)
  - drop giant nested blobs
- `part.type=tool` compaction
  - keep: `callID`, `tool`, `state.status`
  - input: hashes, lengths, bounded previews
  - output: hash, length, bounded preview on failure/error
  - metadata: selected fields (`exit`, `truncated`, `description`)
- `part.type=reasoning` redaction
  - remove encrypted reasoning content field only

## Session Manifest Schema

`session_<id>.manifest.json` includes:

- ingest/runtime scope:
  - `ingest_version`, `source_db_path`, `session_project_id`
  - `scoped_project_ids`, `project_worktree`, `project_names`
- session metadata:
  - `session_id`, `session_directory`, `session_time_created`, `session_time_updated`
- counts:
  - `record_counts`, `part_type_counts`, `total_records`
  - `records_in_current_snapshot`, `records_appended_this_run`, `total_records_in_file`
- file integrity:
  - `jsonl_path`, `jsonl_sha256`, `jsonl_bytes`
- timing:
  - `ingested_at`

## Session Index Row Schema

Each line in `sessions_index.jsonl` includes:

- identifiers: `session_id`, `project_id`, `slug`, `version`
- context: `title`, `directory`
- timestamps:
  - `session_time_created`
  - `session_time_updated`
  - `session_time_archived`
  - `index_record_created_at`
- counts: `message_count`, `part_count`, `todo_count`

## Scope and Contamination Guard

A session must satisfy both:

1. `session.project_id` in project ids resolved for selected worktree
2. `session.directory` under selected worktree path containment

This dual guard prevents cross-project contamination (notably when shared/global project ids are present).

## Non-Goals of This Layer

- Not a semantic event model.
- Not lesson/memory extraction.
- Not interpretation of reasoning quality.
- Not policy/governance decisions.

Those belong to downstream derived layers.
