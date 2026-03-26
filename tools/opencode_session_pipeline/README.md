# OpenCode Session Pipeline Portable Packet

This packet contains the raw ingestion and canonical event normalization pipeline
for OpenCode session logs.

Included tools:

- `bin/ingest_raw.py`
- `bin/normalize_events.py`
- `bin/validate_events.py`
- `bin/history.py`
- `bin/extract_metrics.py`

Schema docs:

- `doc/schemas/opencode_raw_ingestion_v0.md`
- `doc/schemas/opencode_event_v0.md`

## Quick Start

Run from the packet root directory.

For this repository, prefer the wrapper script from repo root:

```bash
./agents/scripts/run_opencode_ingestion.sh
```

This runs ingest -> normalize -> validate with repo-scoped defaults and writes
all archive outputs under `<repo>/archive/`.

1) Ingest raw logs from OpenCode SQLite DB

```bash
python3 bin/ingest_raw.py --mode incremental
```

2) Normalize into canonical events

```bash
python3 bin/normalize_events.py --mode incremental
```

3) Validate event coverage

```bash
python3 bin/validate_events.py
```

4) Query event history

```bash
python3 bin/history.py timeline --session-id <session_id>
python3 bin/history.py tools --session-id <session_id> --failed-only
```

5) Extract evaluator metrics

```bash
python3 bin/extract_metrics.py --session-id <session_id> --pretty
```

This emits a stable metric bundle including:

- token totals (from raw `step-finish` snapshots)
- wall-clock duration
- tool/failure counts
- long/compound bash command counts

## Output Layout

- Raw logs: `archive/raw/opencode/<project>/session_<session_id>.jsonl`
- Raw manifests: `archive/manifests/opencode/<project>/session_<session_id>.manifest.json`
- Raw session index: `archive/index/opencode/<project>/sessions_index.jsonl`
- Canonical events: `archive/derived/events/opencode/<project>/session_<session_id>.events.jsonl`
- Event manifests: `archive/manifests/opencode/<project>/session_<session_id>.events.manifest.json`
- Event index: `archive/index/opencode/<project>/events_index.jsonl`
- Checkpoints:
  - `archive/checkpoints/opencode_ingest_state.json`
  - `archive/checkpoints/opencode_events_state.json`

## Notes

- The pipeline is file-backed (`jsonl` + `json` manifests/index/checkpoints).
- SQLite is source input only (`opencode.db`), not archive storage.
- Keep `archive/` out of git.
