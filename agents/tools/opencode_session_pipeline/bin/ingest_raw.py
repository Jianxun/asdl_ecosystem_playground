#!/usr/bin/env python3
"""OpenCode raw session ingestion (project-scoped, append-only, idempotent).

Purpose
-------
Create a durable, replayable archive of OpenCode sessions for a single repo
scope without cross-project contamination. This script is the raw ingestion
layer (source-like records), not the semantic extraction layer.

Key behaviors
-------------
- Scopes sessions to the current repo by default:
  - resolves worktree from `git rev-parse --show-toplevel`
  - falls back to current working directory if git root is unavailable
- Uses strict scope guards:
  - session must match OpenCode `project` mapping for the worktree
  - session `directory` must be inside the worktree path
- Writes stable per-session files (no timestamp in filename):
  - `archive/raw/opencode/<project_name>/session_<session_id>.jsonl`
  - `archive/manifests/opencode/<project_name>/session_<session_id>.manifest.json`
- Maintains idempotency with `record_fingerprint`:
  - rerunning ingestion does not duplicate existing records
  - ongoing sessions append only newly observed row versions
- Generates a navigation index:
  - `archive/index/opencode/<project_name>/sessions_index.jsonl`
  - includes session title, timestamps, counts, and basic metadata

Compaction and redaction
------------------------
To keep archive size manageable while preserving replay utility:
- `message.data` is compacted (keeps high-value metadata and diff summaries,
  drops huge embedded before/after blobs)
- `part.type=tool` payloads are compacted to command/output hashes, lengths,
  status, and bounded previews for failures
- encrypted reasoning payloads (`reasoningEncryptedContent`) are removed
- redaction metadata is recorded in each archived record (`payload_redaction`)

Important timestamp semantics
-----------------------------
- `session_time_*` fields in index files come from OpenCode's `session` table
- `index_record_created_at` is when this script generated the index row
- `ingested_at` is when this script wrote a particular archived record

Usage examples
--------------
Backfill all in-scope sessions:
    python3 tools/opencode/ingest_raw.py --mode backfill

Incremental ingest (new/updated sessions since checkpoint):
    python3 tools/opencode/ingest_raw.py --mode incremental

Single session ingest:
    python3 tools/opencode/ingest_raw.py --mode session --session-id <session_id>

Preview actions without writing:
    python3 tools/opencode/ingest_raw.py --mode backfill --dry-run

Override defaults (optional):
    python3 tools/opencode/ingest_raw.py \
      --db-path ~/.local/share/opencode/opencode.db \
      --project-worktree /abs/path/to/repo

Notes
-----
- Intended for local archival workflows; keep `archive/` out of git.
- Raw archive is append-only at record level; semantic transforms should run in
  downstream normalized/derived pipelines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


INGEST_VERSION = "v0.1.0"


def detect_default_project_worktree() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if out:
            return str(Path(out).resolve())
    except Exception:
        pass
    return str(Path.cwd().resolve())


@dataclass
class ProjectScope:
    project_ids: list[str]
    worktree: str
    names: list[str]


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n")


def atomic_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=True, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def atomic_write_jsonl_from_lines(path: Path, lines: list[str]) -> None:
    ensure_parent(path)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line)
                f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_existing_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    cur = conn.execute(query, params)
    return cur.fetchall()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def truncate_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[:limit]


def sanitize_message_data(raw_data: str) -> tuple[str, dict[str, Any] | None]:
    try:
        obj = json.loads(raw_data)
    except Exception:
        return raw_data, None

    if not isinstance(obj, dict):
        return raw_data, None

    before_size = len(raw_data)
    out: dict[str, Any] = {}

    keep_top_level = [
        "role",
        "time",
        "parentID",
        "modelID",
        "providerID",
        "mode",
        "agent",
        "path",
        "variant",
        "model",
    ]
    for key in keep_top_level:
        if key in obj:
            out[key] = obj[key]

    summary = obj.get("summary")
    if isinstance(summary, dict):
        compact_summary: dict[str, Any] = {}
        diffs = summary.get("diffs")
        if isinstance(diffs, list):
            compact_diffs = []
            for d in diffs[:200]:
                if not isinstance(d, dict):
                    continue
                compact_diffs.append(
                    {
                        "file": d.get("file"),
                        "status": d.get("status"),
                        "additions": d.get("additions"),
                        "deletions": d.get("deletions"),
                    }
                )
            compact_summary["diffs"] = compact_diffs
            compact_summary["diff_count"] = len(diffs)
        if compact_summary:
            out["summary"] = compact_summary

    sanitized = json.dumps(out, ensure_ascii=True, separators=(",", ":"))
    removed = before_size - len(sanitized)
    redaction = None
    if removed > 0:
        redaction = {
            "type": "message_data_compaction",
            "bytes_removed": removed,
        }
    return sanitized, redaction


def sanitize_tool_part_data(raw_data: str) -> tuple[str, dict[str, Any] | None]:
    try:
        obj = json.loads(raw_data)
    except Exception:
        return raw_data, None
    if not isinstance(obj, dict) or obj.get("type") != "tool":
        return raw_data, None

    before_size = len(raw_data)
    out = {
        "type": "tool",
        "callID": obj.get("callID"),
        "tool": obj.get("tool"),
    }

    state = obj.get("state")
    if isinstance(state, dict):
        s_out: dict[str, Any] = {"status": state.get("status")}

        inp = state.get("input")
        if isinstance(inp, dict):
            compact_input: dict[str, Any] = {}
            if isinstance(inp.get("command"), str):
                cmd = inp["command"]
                compact_input["command_preview"] = truncate_text(cmd, 500)
                compact_input["command_sha256"] = sha256_text(cmd)
                compact_input["command_len"] = len(cmd)
            if isinstance(inp.get("description"), str):
                compact_input["description"] = truncate_text(inp["description"], 300)
            if isinstance(inp.get("patchText"), str):
                patch = inp["patchText"]
                compact_input["patch_sha256"] = sha256_text(patch)
                compact_input["patch_len"] = len(patch)
            if compact_input:
                s_out["input"] = compact_input

        out_text = state.get("output")
        metadata_obj = state.get("metadata")
        metadata: dict[str, Any] = metadata_obj if isinstance(metadata_obj, dict) else {}
        exit_code = metadata.get("exit")
        status = state.get("status")
        keep_output = status in {"failed", "error"} or (isinstance(exit_code, int) and exit_code != 0)
        if isinstance(out_text, str):
            s_out["output_sha256"] = sha256_text(out_text)
            s_out["output_len"] = len(out_text)
            if keep_output:
                s_out["output_preview"] = truncate_text(out_text, 4000)

        if metadata:
            compact_meta = {
                "exit": metadata.get("exit"),
                "truncated": metadata.get("truncated"),
                "description": metadata.get("description"),
            }
            s_out["metadata"] = compact_meta

        timing = state.get("time")
        if isinstance(timing, dict):
            s_out["time"] = {
                "start": timing.get("start"),
                "end": timing.get("end"),
            }

        out["state"] = s_out

    meta = obj.get("metadata")
    if isinstance(meta, dict):
        out["metadata"] = meta

    sanitized = json.dumps(out, ensure_ascii=True, separators=(",", ":"))
    removed = before_size - len(sanitized)
    redaction = None
    if removed > 0:
        redaction = {
            "type": "tool_part_compaction",
            "bytes_removed": removed,
        }
    return sanitized, redaction


def sanitize_payload(source_table: str, payload_raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Drop non-actionable encrypted reasoning blobs while keeping useful hints.

    We keep a deterministic sanitized payload for archive/replay use, and track
    a redaction descriptor for transparency.
    """
    sanitized = dict(payload_raw)

    if source_table == "message":
        data = sanitized.get("data")
        if isinstance(data, str):
            compact_data, redaction = sanitize_message_data(data)
            sanitized["data"] = compact_data
            return sanitized, redaction
        return sanitized, None

    if source_table != "part":
        return sanitized, None

    data = sanitized.get("data")
    if not isinstance(data, str):
        return sanitized, None

    try:
        parsed = json.loads(data)
    except Exception:
        return sanitized, None

    if not isinstance(parsed, dict):
        return sanitized, None

    if parsed.get("type") == "tool":
        compact_data, redaction = sanitize_tool_part_data(data)
        sanitized["data"] = compact_data
        return sanitized, redaction

    if parsed.get("type") != "reasoning":
        return sanitized, None

    metadata = parsed.get("metadata")
    if not isinstance(metadata, dict):
        return sanitized, None

    openai_meta = metadata.get("openai")
    if not isinstance(openai_meta, dict):
        return sanitized, None

    encrypted = openai_meta.get("reasoningEncryptedContent")
    if not isinstance(encrypted, str):
        return sanitized, None

    encrypted_len = len(encrypted)
    del openai_meta["reasoningEncryptedContent"]

    if not openai_meta:
        metadata.pop("openai", None)
    if not metadata:
        parsed.pop("metadata", None)

    sanitized["data"] = json.dumps(parsed, ensure_ascii=True, separators=(",", ":"))
    redaction = {
        "type": "reasoning_encrypted_content",
        "bytes_removed": encrypted_len,
        "part_type": "reasoning",
    }
    return sanitized, redaction


def resolve_project_scope(conn: sqlite3.Connection, worktree: str) -> ProjectScope:
    found = rows(
        conn,
        """
        SELECT id, worktree, name
        FROM project
        WHERE worktree = ?
        ORDER BY time_updated DESC, id DESC
        """,
        (worktree,),
    )
    if not found:
        known = rows(conn, "SELECT id, worktree, name FROM project ORDER BY time_updated DESC")
        known_fmt = [f"{r['id']} :: {r['worktree']} :: {r['name'] or ''}" for r in known]
        msg = "No matching project for worktree. Known projects:\n- " + "\n- ".join(known_fmt)
        raise RuntimeError(msg)

    return ProjectScope(
        project_ids=[str(r["id"]) for r in found],
        worktree=worktree,
        names=[str(r["name"]) for r in found if r["name"]],
    )


def load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "entries": {}}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def checkpoint_key(db_path: Path, worktree: str) -> str:
    return sha256_text(f"{db_path.resolve()}|{Path(worktree).resolve()}")


def session_directory_clause() -> str:
    return "(directory = ? OR directory LIKE ?)"


def session_directory_params(worktree: str) -> tuple[str, str]:
    base = str(Path(worktree).expanduser().resolve())
    return (base, f"{base}/%")


def is_directory_in_scope(directory: str | None, worktree: str) -> bool:
    if not directory:
        return False
    try:
        session_dir = Path(directory).expanduser().resolve()
        root_dir = Path(worktree).expanduser().resolve()
        return os.path.commonpath([str(session_dir), str(root_dir)]) == str(root_dir)
    except Exception:
        return False


def get_incremental_cursor(state: dict[str, Any], key: str) -> tuple[int | None, str | None]:
    entry = state.get("entries", {}).get(key)
    if not entry:
        return None, None
    return entry.get("last_session_time_updated"), entry.get("last_session_id")


def put_incremental_cursor(
    state: dict[str, Any],
    key: str,
    time_updated: int,
    session_id: str,
) -> None:
    state.setdefault("entries", {})[key] = {
        "last_session_time_updated": time_updated,
        "last_session_id": session_id,
        "updated_at": utc_now_iso(),
        "ingest_version": INGEST_VERSION,
    }


def select_scoped_sessions(
    conn: sqlite3.Connection,
    project_ids: list[str],
    project_worktree: str,
    mode: str,
    session_ids: list[str],
    cursor_time_updated: int | None,
    cursor_session_id: str | None,
) -> list[sqlite3.Row]:
    if not project_ids:
        return []
    project_placeholders = ",".join(["?"] * len(project_ids))
    dir_clause = session_directory_clause()
    dir_params = session_directory_params(project_worktree)

    if mode == "session":
        if not session_ids:
            raise RuntimeError("Mode=session requires at least one --session-id")
        session_placeholders = ",".join(["?"] * len(session_ids))
        return rows(
            conn,
            f"""
            SELECT *
            FROM session
            WHERE project_id IN ({project_placeholders})
              AND {dir_clause}
              AND id IN ({session_placeholders})
            ORDER BY time_created ASC, id ASC
            """,
            (*project_ids, *dir_params, *session_ids),
        )

    if mode == "incremental":
        if cursor_time_updated is None or cursor_session_id is None:
            return rows(
            conn,
            f"""
                SELECT *
                FROM session
                WHERE project_id IN ({project_placeholders})
                  AND {dir_clause}
                ORDER BY time_updated ASC, id ASC
                """,
                (*project_ids, *dir_params),
            )
        return rows(
            conn,
            f"""
            SELECT *
            FROM session
            WHERE project_id IN ({project_placeholders})
              AND {dir_clause}
              AND (
                time_updated > ?
                OR (time_updated = ? AND id > ?)
              )
            ORDER BY time_updated ASC, id ASC
            """,
            (*project_ids, *dir_params, cursor_time_updated, cursor_time_updated, cursor_session_id),
        )

    return rows(
        conn,
        f"""
        SELECT *
        FROM session
        WHERE project_id IN ({project_placeholders})
          AND {dir_clause}
        ORDER BY time_created ASC, id ASC
        """,
        (*project_ids, *dir_params),
    )


def counts_by_session(conn: sqlite3.Connection, table: str, session_ids: list[str]) -> dict[str, int]:
    if not session_ids:
        return {}
    placeholders = ",".join(["?"] * len(session_ids))
    out: dict[str, int] = {}
    for r in rows(
        conn,
        f"""
        SELECT session_id, COUNT(*) AS c
        FROM {table}
        WHERE session_id IN ({placeholders})
        GROUP BY session_id
        """,
        tuple(session_ids),
    ):
        out[str(r["session_id"])] = int(r["c"])
    return out


def build_session_index_rows(
    conn: sqlite3.Connection,
    scope: ProjectScope,
) -> list[dict[str, Any]]:
    indexed_at = utc_now_iso()
    scoped_sessions = select_scoped_sessions(
        conn,
        scope.project_ids,
        scope.worktree,
        mode="backfill",
        session_ids=[],
        cursor_time_updated=None,
        cursor_session_id=None,
    )
    sids = [str(r["id"]) for r in scoped_sessions]
    msg_counts = counts_by_session(conn, "message", sids)
    part_counts = counts_by_session(conn, "part", sids)
    todo_counts = counts_by_session(conn, "todo", sids)

    entries: list[dict[str, Any]] = []
    for srow in scoped_sessions:
        s = row_to_dict(srow)
        sid = str(s["id"])
        entries.append(
            {
                "session_id": sid,
                "title": s.get("title"),
                "project_id": s.get("project_id"),
                "directory": s.get("directory"),
                "slug": s.get("slug"),
                "version": s.get("version"),
                "session_time_created": s.get("time_created"),
                "session_time_updated": s.get("time_updated"),
                "session_time_archived": s.get("time_archived"),
                "message_count": msg_counts.get(sid, 0),
                "part_count": part_counts.get(sid, 0),
                "todo_count": todo_counts.get(sid, 0),
                "index_record_created_at": indexed_at,
            }
        )

    entries.sort(
        key=lambda x: (
            -1 if x.get("session_time_updated") is None else -int(x["session_time_updated"]),
            "" if x.get("session_id") is None else str(x["session_id"]),
        )
    )
    return entries


def write_session_index(
    conn: sqlite3.Connection,
    scope: ProjectScope,
    index_root: Path,
    project_label: str,
    source_db_path: Path,
) -> Path:
    entries = build_session_index_rows(conn, scope)
    index_path = index_root / "opencode" / project_label / "sessions_index.jsonl"
    lines = [json.dumps(e, ensure_ascii=True, separators=(",", ":")) for e in entries]
    atomic_write_jsonl_from_lines(index_path, lines)

    manifest_path = index_root / "opencode" / project_label / "sessions_index.manifest.json"
    manifest = {
        "schema_version": 2,
        "ingest_version": INGEST_VERSION,
        "project_worktree": scope.worktree,
        "project_ids": scope.project_ids,
        "project_names": scope.names,
        "source_db_path": str(source_db_path),
        "session_count": len(entries),
        "updated_at": utc_now_iso(),
        "index_path": str(index_path),
        "index_sha256": sha256_file(index_path),
        "index_bytes": index_path.stat().st_size,
        "field_notes": {
            "session_time_*": "Timestamps from OpenCode session table",
            "index_record_created_at": "When this index row was generated",
        },
    }
    atomic_write_json(manifest_path, manifest)
    return index_path


def build_record(
    *,
    record_type: str,
    source_table: str,
    row_id: str,
    project_id: str,
    session_id: str,
    source_db_path: str,
    payload_raw: dict[str, Any],
    ingested_at: str,
) -> dict[str, Any]:
    source_payload_text = canonical_json(payload_raw)
    source_payload_sha = sha256_text(source_payload_text)
    sanitized_payload, redaction = sanitize_payload(source_table, payload_raw)
    payload_text = canonical_json(sanitized_payload)
    payload_sha = sha256_text(payload_text)
    record_fingerprint = sha256_text(
        f"{source_table}|{row_id}|{payload_raw.get('time_updated')}|{source_payload_sha}"
    )
    return {
        "record_type": record_type,
        "source_table": source_table,
        "row_id": row_id,
        "project_id": project_id,
        "session_id": session_id,
        "time_created": payload_raw.get("time_created"),
        "time_updated": payload_raw.get("time_updated"),
        "ingested_at": ingested_at,
        "source_db_path": source_db_path,
        "payload_raw": sanitized_payload,
        "payload_sha256": payload_sha,
        "source_payload_sha256": source_payload_sha,
        "record_fingerprint": record_fingerprint,
        "payload_redaction": redaction,
        "ingest_version": INGEST_VERSION,
    }


def parse_part_type(part_data: str) -> str:
    try:
        obj = json.loads(part_data)
        if isinstance(obj, dict) and isinstance(obj.get("type"), str):
            return obj["type"]
    except Exception:
        pass
    return "unknown"


def export_session(
    conn: sqlite3.Connection,
    scope: ProjectScope,
    session_row: sqlite3.Row,
    source_db_path: Path,
    include_todo: bool,
    ingested_at: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    s = row_to_dict(session_row)
    session_id = s["id"]
    session_project_id = str(s["project_id"])

    records: list[dict[str, Any]] = []
    type_counts: Counter[str] = Counter()
    part_type_counts: Counter[str] = Counter()

    records.append(
        build_record(
            record_type="session",
            source_table="session",
            row_id=str(session_id),
            project_id=session_project_id,
            session_id=session_id,
            source_db_path=str(source_db_path),
            payload_raw=s,
            ingested_at=ingested_at,
        )
    )
    type_counts["session"] += 1

    message_rows = rows(
        conn,
        """
        SELECT *
        FROM message
        WHERE session_id = ?
        ORDER BY time_created ASC, id ASC
        """,
        (session_id,),
    )
    for mrow in message_rows:
        m = row_to_dict(mrow)
        records.append(
            build_record(
                record_type="message",
                source_table="message",
                row_id=str(m["id"]),
                project_id=session_project_id,
                session_id=session_id,
                source_db_path=str(source_db_path),
                payload_raw=m,
                ingested_at=ingested_at,
            )
        )
        type_counts["message"] += 1

    part_rows = rows(
        conn,
        """
        SELECT *
        FROM part
        WHERE session_id = ?
        ORDER BY time_created ASC, id ASC
        """,
        (session_id,),
    )
    for prow in part_rows:
        p = row_to_dict(prow)
        records.append(
            build_record(
                record_type="part",
                source_table="part",
                row_id=str(p["id"]),
                project_id=session_project_id,
                session_id=session_id,
                source_db_path=str(source_db_path),
                payload_raw=p,
                ingested_at=ingested_at,
            )
        )
        type_counts["part"] += 1
        if isinstance(p.get("data"), str):
            part_type_counts[parse_part_type(p["data"])] += 1

    if include_todo:
        todo_rows = rows(
            conn,
            """
            SELECT *
            FROM todo
            WHERE session_id = ?
            ORDER BY position ASC
            """,
            (session_id,),
        )
        for trow in todo_rows:
            t = row_to_dict(trow)
            rid = f"{t['session_id']}:{t['position']}"
            records.append(
                build_record(
                    record_type="todo",
                    source_table="todo",
                    row_id=rid,
                    project_id=session_project_id,
                    session_id=session_id,
                    source_db_path=str(source_db_path),
                    payload_raw=t,
                    ingested_at=ingested_at,
                )
            )
            type_counts["todo"] += 1

    manifest = {
        "ingest_version": INGEST_VERSION,
        "source_db_path": str(source_db_path),
        "session_project_id": session_project_id,
        "scoped_project_ids": scope.project_ids,
        "project_worktree": scope.worktree,
        "project_names": scope.names,
        "session_id": session_id,
        "session_directory": s.get("directory"),
        "session_time_created": s.get("time_created"),
        "session_time_updated": s.get("time_updated"),
        "record_counts": dict(type_counts),
        "part_type_counts": dict(part_type_counts),
        "total_records": len(records),
        "ingested_at": ingested_at,
    }
    return records, manifest


def output_paths(
    archive_root: Path,
    manifest_root: Path,
    project_label: str,
    session_id: str,
) -> tuple[Path, Path]:
    base = f"session_{session_id}"
    jsonl_path = archive_root / project_label / f"{base}.jsonl"
    manifest_path = manifest_root / project_label / f"{base}.manifest.json"
    return jsonl_path, manifest_path


def fingerprint_of_record(record: dict[str, Any]) -> str | None:
    if isinstance(record.get("record_fingerprint"), str):
        return str(record["record_fingerprint"])
    source_table = record.get("source_table")
    row_id = record.get("row_id")
    time_updated = record.get("time_updated")
    payload_sha = record.get("source_payload_sha256") or record.get("payload_sha256")
    if source_table is None or row_id is None or payload_sha is None:
        return None
    return sha256_text(f"{source_table}|{row_id}|{time_updated}|{payload_sha}")


def stable_record_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    time_created = record.get("time_created")
    source_table = record.get("source_table")
    row_id = record.get("row_id")
    time_updated = record.get("time_updated")
    fp = record.get("record_fingerprint")
    return (
        -1 if time_created is None else int(time_created),
        "" if source_table is None else str(source_table),
        "" if row_id is None else str(row_id),
        -1 if time_updated is None else int(time_updated),
        "" if fp is None else str(fp),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract project-scoped raw logs from OpenCode SQLite DB")
    parser.add_argument("--mode", choices=["backfill", "incremental", "session"], default="incremental")
    parser.add_argument(
        "--db-path",
        default="/Users/jianxunzhu/.local/share/opencode/opencode.db",
        help="Path to opencode.db",
    )
    parser.add_argument(
        "--project-worktree",
        default=detect_default_project_worktree(),
        help="Project worktree used to scope sessions (defaults to git repo root)",
    )
    parser.add_argument(
        "--archive-root",
        default="archive/raw/opencode",
        help="Root directory for JSONL records",
    )
    parser.add_argument(
        "--manifest-root",
        default="archive/manifests/opencode",
        help="Root directory for manifest files",
    )
    parser.add_argument(
        "--checkpoint-path",
        default="archive/checkpoints/opencode_ingest_state.json",
        help="Incremental checkpoint state file",
    )
    parser.add_argument(
        "--index-root",
        default="archive/index",
        help="Root directory for session index artifacts",
    )
    parser.add_argument("--session-id", action="append", default=[], help="Session ID (repeatable) for mode=session")
    parser.add_argument("--include-todo", dest="include_todo", action="store_true", default=True)
    parser.add_argument("--no-include-todo", dest="include_todo", action="store_false")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path).expanduser().resolve()
    archive_root = Path(args.archive_root)
    manifest_root = Path(args.manifest_root)
    checkpoint_path = Path(args.checkpoint_path)
    index_root = Path(args.index_root)

    if not db_path.exists():
        print(f"ERROR: DB not found: {db_path}", file=sys.stderr)
        return 2

    ingested_at = utc_now_iso()

    with connect_db(db_path) as conn:
        scope = resolve_project_scope(conn, str(Path(args.project_worktree).expanduser().resolve()))

        cp_state = load_checkpoint(checkpoint_path)
        cp_key = checkpoint_key(db_path, scope.worktree)
        cp_time, cp_session_id = get_incremental_cursor(cp_state, cp_key)

        scoped_sessions = select_scoped_sessions(
            conn,
            scope.project_ids,
            scope.worktree,
            args.mode,
            args.session_id,
            cp_time,
            cp_session_id,
        )

        if args.mode == "session" and args.session_id:
            found_ids = {s["id"] for s in scoped_sessions}
            missing = [sid for sid in args.session_id if sid not in found_ids]
            if missing:
                print(
                    "ERROR: Some --session-id values are not in the scoped project: " + ", ".join(missing),
                    file=sys.stderr,
                )
                return 2

        if not scoped_sessions:
            print("No scoped sessions to export.")
            return 0

        project_label = Path(scope.worktree).name

        max_cursor: tuple[int, str] | None = None
        total_records_scanned = 0
        total_records_appended = 0
        session_count = 0

        for srow in scoped_sessions:
            if str(srow["project_id"]) not in set(scope.project_ids):
                raise RuntimeError(f"Contamination guard failed: session {srow['id']} is out of scope")
            if not is_directory_in_scope(srow["directory"], scope.worktree):
                raise RuntimeError(
                    f"Contamination guard failed: session {srow['id']} has directory {srow['directory']} outside {scope.worktree}"
                )

            records, manifest = export_session(
                conn=conn,
                scope=scope,
                session_row=srow,
                source_db_path=db_path,
                include_todo=args.include_todo,
                ingested_at=ingested_at,
            )

            jsonl_path, manifest_path = output_paths(
                archive_root=archive_root,
                manifest_root=manifest_root,
                project_label=project_label,
                session_id=srow["id"],
            )

            if args.dry_run:
                print(
                    f"DRY-RUN export session={srow['id']} records={len(records)} jsonl={jsonl_path} manifest={manifest_path}"
                )
                total_records_appended += len(records)
            else:
                existing_records = load_existing_jsonl(jsonl_path)
                existing_fingerprints = {
                    fp for fp in (fingerprint_of_record(rec) for rec in existing_records) if fp is not None
                }
                new_records: list[dict[str, Any]] = []
                for rec in records:
                    rec_fp = fingerprint_of_record(rec)
                    if rec_fp is None:
                        continue
                    if rec_fp not in existing_fingerprints:
                        new_records.append(rec)

                if new_records:
                    combined = existing_records + new_records
                    combined.sort(key=stable_record_sort_key)
                    atomic_write_jsonl(jsonl_path, combined)

                    file_hash = sha256_file(jsonl_path)
                    file_bytes = jsonl_path.stat().st_size

                    manifest["jsonl_path"] = str(jsonl_path)
                    manifest["jsonl_sha256"] = file_hash
                    manifest["jsonl_bytes"] = file_bytes
                    manifest["records_in_current_snapshot"] = len(records)
                    manifest["records_appended_this_run"] = len(new_records)
                    manifest["total_records_in_file"] = len(combined)
                    atomic_write_json(manifest_path, manifest)

                    if args.verbose:
                        print(
                            f"UPDATED session={srow['id']} appended={len(new_records)} total={len(combined)} -> {jsonl_path}"
                        )
                    total_records_appended += len(new_records)
                else:
                    if jsonl_path.exists():
                        file_hash = sha256_file(jsonl_path)
                        file_bytes = jsonl_path.stat().st_size
                        manifest["jsonl_path"] = str(jsonl_path)
                        manifest["jsonl_sha256"] = file_hash
                        manifest["jsonl_bytes"] = file_bytes
                        manifest["records_in_current_snapshot"] = len(records)
                        manifest["records_appended_this_run"] = 0
                        manifest["total_records_in_file"] = len(existing_records)
                    else:
                        # First write for a session with no pre-existing file.
                        records.sort(key=stable_record_sort_key)
                        atomic_write_jsonl(jsonl_path, records)
                        file_hash = sha256_file(jsonl_path)
                        file_bytes = jsonl_path.stat().st_size
                        manifest["jsonl_path"] = str(jsonl_path)
                        manifest["jsonl_sha256"] = file_hash
                        manifest["jsonl_bytes"] = file_bytes
                        manifest["records_in_current_snapshot"] = len(records)
                        manifest["records_appended_this_run"] = len(records)
                        manifest["total_records_in_file"] = len(records)

                    atomic_write_json(manifest_path, manifest)

                    if args.verbose:
                        print(
                            f"UPDATED session={srow['id']} appended={manifest['records_appended_this_run']} total={manifest['total_records_in_file']} -> {jsonl_path}"
                        )
                    total_records_appended += int(manifest["records_appended_this_run"])

            total_records_scanned += len(records)
            session_count += 1

            cur = (int(srow["time_updated"]), str(srow["id"]))
            if max_cursor is None or cur > max_cursor:
                max_cursor = cur

        if (args.mode in {"incremental", "backfill"}) and max_cursor is not None and not args.dry_run:
            put_incremental_cursor(cp_state, cp_key, max_cursor[0], max_cursor[1])
            atomic_write_json(checkpoint_path, cp_state)

        index_path: Path | None = None
        if not args.dry_run:
            index_path = write_session_index(
                conn=conn,
                scope=scope,
                index_root=index_root,
                project_label=project_label,
                source_db_path=db_path,
            )

        print(
            f"Done. worktree={scope.worktree} project_ids={scope.project_ids} mode={args.mode} sessions={session_count} scanned_records={total_records_scanned} appended_records={total_records_appended} dry_run={args.dry_run}"
        )
        if index_path is not None:
            print(f"Session index updated: {index_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
