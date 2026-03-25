#!/usr/bin/env python3
"""Normalize OpenCode raw session logs into canonical event timelines.

This script consumes files produced by tools/opencode/ingest_raw.py and emits
deterministic, per-session canonical events for replay, analysis, and downstream
memory/lesson extraction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "opencode_event_v0"
NORMALIZER_VERSION = "v0.1.0"
TOOL_FAILURE_STATUS = {"failed", "error"}
VALIDATION_HINTS = (
    "pytest",
    "npm test",
    "pnpm test",
    "yarn test",
    "bun test",
    "go test",
    "cargo test",
)


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


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def atomic_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")))
                f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


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


def parse_session_id_from_raw_path(path: Path) -> str | None:
    name = path.name
    prefix = "session_"
    suffix = ".jsonl"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return None
    body = name[len(prefix) : -len(suffix)]
    return body or None


def parse_maybe_json_str(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, str):
        return None
    try:
        obj = json.loads(value)
    except Exception:
        return None
    if isinstance(obj, dict):
        return obj
    return None


def to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def stable_record_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -1 if record.get("time_created") is None else int(record["time_created"]),
        "" if record.get("source_table") is None else str(record["source_table"]),
        "" if record.get("row_id") is None else str(record["row_id"]),
        -1 if record.get("time_updated") is None else int(record["time_updated"]),
        "" if record.get("record_fingerprint") is None else str(record["record_fingerprint"]),
    )


def stable_event_sort_key(event: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -1 if event.get("event_time") is None else int(event["event_time"]),
        "" if event.get("event_type") is None else str(event["event_type"]),
        "" if event.get("event_fingerprint") is None else str(event["event_fingerprint"]),
    )


def build_base_event(
    *,
    session_id: str,
    project_label: str,
    event_type: str,
    actor_role: str,
    payload_compact: dict[str, Any],
    raw_record: dict[str, Any],
    status: str | None = None,
    severity: str | None = None,
    event_time: int | None = None,
) -> dict[str, Any]:
    provenance = {
        "source_table": raw_record.get("source_table"),
        "row_id": raw_record.get("row_id"),
        "record_type": raw_record.get("record_type"),
        "record_fingerprint": raw_record.get("record_fingerprint"),
        "source_payload_sha256": raw_record.get("source_payload_sha256"),
        "payload_sha256": raw_record.get("payload_sha256"),
        "time_created": raw_record.get("time_created"),
        "time_updated": raw_record.get("time_updated"),
    }
    if event_time is None:
        event_time = to_int_or_none(raw_record.get("time_created")) or to_int_or_none(raw_record.get("time_updated"))

    payload_hash = sha256_text(canonical_json(payload_compact))
    fingerprint_source = "|".join(
        [
            session_id,
            event_type,
            "" if event_time is None else str(event_time),
            "" if provenance.get("record_fingerprint") is None else str(provenance["record_fingerprint"]),
            payload_hash,
        ]
    )
    event_fingerprint = sha256_text(fingerprint_source)

    event = {
        "event_id": f"evt_{event_fingerprint[:16]}",
        "event_fingerprint": event_fingerprint,
        "schema_version": SCHEMA_VERSION,
        "normalizer_version": NORMALIZER_VERSION,
        "session_id": session_id,
        "project_label": project_label,
        "seq": 0,
        "event_type": event_type,
        "event_time": event_time,
        "record_time": raw_record.get("ingested_at"),
        "actor_role": actor_role,
        "payload_compact": payload_compact,
        "provenance": provenance,
    }
    if status is not None:
        event["status"] = status
    if severity is not None:
        event["severity"] = severity
    return event


def maybe_emit_validation_event(
    *,
    session_id: str,
    project_label: str,
    raw_record: dict[str, Any],
    tool_payload: dict[str, Any],
) -> dict[str, Any] | None:
    state = tool_payload.get("state") if isinstance(tool_payload.get("state"), dict) else {}
    inp = state.get("input") if isinstance(state.get("input"), dict) else {}
    command_preview = inp.get("command_preview")
    if not isinstance(command_preview, str):
        return None
    lower = command_preview.lower()
    if not any(hint in lower for hint in VALIDATION_HINTS):
        return None

    metadata = state.get("metadata") if isinstance(state.get("metadata"), dict) else {}
    exit_code = metadata.get("exit")
    status = state.get("status")
    passed = (isinstance(exit_code, int) and exit_code == 0) or (status == "completed" and exit_code in (None, 0))

    payload = {
        "validator_kind": "tool_command_heuristic",
        "tool": tool_payload.get("tool"),
        "call_id": tool_payload.get("callID"),
        "command_preview": command_preview,
        "command_sha256": inp.get("command_sha256"),
        "exit_code": exit_code,
        "passed": passed,
    }
    return build_base_event(
        session_id=session_id,
        project_label=project_label,
        event_type="validation_result",
        actor_role="system",
        payload_compact=payload,
        raw_record=raw_record,
        status="passed" if passed else "failed",
        severity="info" if passed else "warning",
    )


def normalize_session_records(session_id: str, project_label: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records_sorted = sorted(records, key=stable_record_sort_key)
    events: list[dict[str, Any]] = []

    seen_session_started = False
    seen_session_archived = False
    todo_state_by_position: dict[str, str] = {}

    for rec in records_sorted:
        record_type = rec.get("record_type")
        payload_raw = rec.get("payload_raw") if isinstance(rec.get("payload_raw"), dict) else {}

        if record_type == "session":
            if not seen_session_started:
                seen_session_started = True
                events.append(
                    build_base_event(
                        session_id=session_id,
                        project_label=project_label,
                        event_type="session_started",
                        actor_role="system",
                        payload_compact={
                            "title": payload_raw.get("title"),
                            "directory": payload_raw.get("directory"),
                            "slug": payload_raw.get("slug"),
                            "version": payload_raw.get("version"),
                        },
                        raw_record=rec,
                        status="observed",
                        severity="info",
                    )
                )

            if payload_raw.get("time_archived") is not None and not seen_session_archived:
                seen_session_archived = True
                events.append(
                    build_base_event(
                        session_id=session_id,
                        project_label=project_label,
                        event_type="session_archived",
                        actor_role="system",
                        payload_compact={"time_archived": payload_raw.get("time_archived")},
                        raw_record=rec,
                        status="archived",
                        severity="info",
                        event_time=to_int_or_none(payload_raw.get("time_archived")),
                    )
                )
            continue

        if record_type == "message":
            data = parse_maybe_json_str(payload_raw.get("data"))
            role = None
            msg_time = None
            if data:
                role = data.get("role") if isinstance(data.get("role"), str) else None
                msg_time = to_int_or_none(data.get("time"))
            role = role or (payload_raw.get("role") if isinstance(payload_raw.get("role"), str) else None)

            event_type = "message_observed"
            actor_role = "system"
            if role == "user":
                event_type = "user_turn"
                actor_role = "user"
            elif role == "assistant":
                event_type = "assistant_turn"
                actor_role = "assistant"

            turn_payload = {
                "message_id": payload_raw.get("id") or rec.get("row_id"),
                "parent_id": (data or {}).get("parentID") if data else None,
                "role": role,
                "model_id": (data or {}).get("modelID") if data else None,
                "provider_id": (data or {}).get("providerID") if data else None,
                "mode": (data or {}).get("mode") if data else None,
                "agent": (data or {}).get("agent") if data else None,
                "path": (data or {}).get("path") if data else None,
            }
            events.append(
                build_base_event(
                    session_id=session_id,
                    project_label=project_label,
                    event_type=event_type,
                    actor_role=actor_role,
                    payload_compact=turn_payload,
                    raw_record=rec,
                    status="observed",
                    severity="info",
                    event_time=msg_time,
                )
            )

            summary = (data or {}).get("summary") if data else None
            diffs = summary.get("diffs") if isinstance(summary, dict) else None
            if isinstance(diffs, list) and diffs:
                events.append(
                    build_base_event(
                        session_id=session_id,
                        project_label=project_label,
                        event_type="artifact_batch_changed",
                        actor_role="assistant",
                        payload_compact={
                            "message_id": payload_raw.get("id") or rec.get("row_id"),
                            "diff_count": summary.get("diff_count") if isinstance(summary, dict) else len(diffs),
                            "diffs": diffs[:50],
                        },
                        raw_record=rec,
                        status="observed",
                        severity="info",
                        event_time=msg_time,
                    )
                )
            continue

        if record_type == "part":
            data = parse_maybe_json_str(payload_raw.get("data"))
            if not data:
                continue
            if data.get("type") != "tool":
                continue

            state = data.get("state") if isinstance(data.get("state"), dict) else {}
            inp = state.get("input") if isinstance(state.get("input"), dict) else {}
            metadata = state.get("metadata") if isinstance(state.get("metadata"), dict) else {}
            timing = state.get("time") if isinstance(state.get("time"), dict) else {}
            status = state.get("status") if isinstance(state.get("status"), str) else None
            exit_code = metadata.get("exit") if isinstance(metadata.get("exit"), int) else metadata.get("exit")

            payload = {
                "call_id": data.get("callID"),
                "tool": data.get("tool"),
                "status": status,
                "exit_code": exit_code,
                "input": {
                    "description": inp.get("description"),
                    "command_preview": inp.get("command_preview"),
                    "command_sha256": inp.get("command_sha256"),
                    "command_len": inp.get("command_len"),
                    "patch_sha256": inp.get("patch_sha256"),
                    "patch_len": inp.get("patch_len"),
                },
                "output": {
                    "output_sha256": state.get("output_sha256"),
                    "output_len": state.get("output_len"),
                },
                "timing": {
                    "start": timing.get("start"),
                    "end": timing.get("end"),
                },
            }
            events.append(
                build_base_event(
                    session_id=session_id,
                    project_label=project_label,
                    event_type="tool_execution",
                    actor_role="tool",
                    payload_compact=payload,
                    raw_record=rec,
                    status=status or "observed",
                    severity="info",
                    event_time=to_int_or_none(timing.get("end")) or to_int_or_none(timing.get("start")),
                )
            )

            failed = (status in TOOL_FAILURE_STATUS) or (isinstance(exit_code, int) and exit_code != 0)
            if failed:
                events.append(
                    build_base_event(
                        session_id=session_id,
                        project_label=project_label,
                        event_type="tool_failure",
                        actor_role="tool",
                        payload_compact={
                            "call_id": data.get("callID"),
                            "tool": data.get("tool"),
                            "status": status,
                            "exit_code": exit_code,
                            "output_preview": state.get("output_preview"),
                        },
                        raw_record=rec,
                        status="failed",
                        severity="warning",
                        event_time=to_int_or_none(timing.get("end")) or to_int_or_none(timing.get("start")),
                    )
                )

            validation_event = maybe_emit_validation_event(
                session_id=session_id,
                project_label=project_label,
                raw_record=rec,
                tool_payload=data,
            )
            if validation_event is not None:
                events.append(validation_event)
            continue

        if record_type == "todo":
            position = payload_raw.get("position")
            pos_key = str(position) if position is not None else str(rec.get("row_id"))
            state_payload = {
                "position": position,
                "content": payload_raw.get("content"),
                "status": payload_raw.get("status"),
                "priority": payload_raw.get("priority"),
            }
            state_hash = sha256_text(canonical_json(state_payload))
            if todo_state_by_position.get(pos_key) == state_hash:
                continue
            todo_state_by_position[pos_key] = state_hash
            events.append(
                build_base_event(
                    session_id=session_id,
                    project_label=project_label,
                    event_type="todo_state_changed",
                    actor_role="system",
                    payload_compact=state_payload,
                    raw_record=rec,
                    status="updated",
                    severity="info",
                )
            )

    events.sort(key=stable_event_sort_key)
    for idx, event in enumerate(events, start=1):
        event["seq"] = idx
    return events


def load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "entries": {}}
    return load_json(path)


def checkpoint_key(worktree: str, project_label: str) -> str:
    return sha256_text(f"{Path(worktree).resolve()}|{project_label}|{SCHEMA_VERSION}")


def get_checkpoint_entry(state: dict[str, Any], key: str) -> dict[str, Any]:
    return state.get("entries", {}).get(key, {})


def put_checkpoint_entry(state: dict[str, Any], key: str, session_file_hashes: dict[str, str]) -> None:
    state.setdefault("entries", {})[key] = {
        "schema_version": SCHEMA_VERSION,
        "normalizer_version": NORMALIZER_VERSION,
        "updated_at": utc_now_iso(),
        "session_file_hashes": session_file_hashes,
    }


def build_event_index_rows(events_project_dir: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for event_file in sorted(events_project_dir.glob("session_*.events.jsonl")):
        session_id = event_file.name[len("session_") : -len(".events.jsonl")]
        rows = load_jsonl(event_file)
        type_counts: Counter[str] = Counter()
        failures = 0
        first_time = None
        last_time = None
        for row in rows:
            et = row.get("event_type")
            if isinstance(et, str):
                type_counts[et] += 1
            if row.get("event_type") == "tool_failure":
                failures += 1
            t = to_int_or_none(row.get("event_time"))
            if t is None:
                continue
            if first_time is None or t < first_time:
                first_time = t
            if last_time is None or t > last_time:
                last_time = t

        entries.append(
            {
                "session_id": session_id,
                "event_count": len(rows),
                "event_type_counts": dict(type_counts),
                "tool_failure_count": failures,
                "first_event_time": first_time,
                "last_event_time": last_time,
                "index_record_created_at": utc_now_iso(),
            }
        )
    entries.sort(key=lambda x: (-(x.get("last_event_time") or -1), x.get("session_id") or ""))
    return entries


def write_events_index(index_root: Path, project_label: str, source_root: Path) -> Path:
    events_dir = source_root / project_label
    entries = build_event_index_rows(events_dir)
    out_path = index_root / "opencode" / project_label / "events_index.jsonl"
    atomic_write_jsonl(out_path, entries)

    manifest = {
        "schema_version": 1,
        "event_schema_version": SCHEMA_VERSION,
        "normalizer_version": NORMALIZER_VERSION,
        "project_label": project_label,
        "event_session_count": len(entries),
        "updated_at": utc_now_iso(),
        "index_path": str(out_path),
        "index_sha256": sha256_file(out_path),
        "index_bytes": out_path.stat().st_size,
    }
    manifest_path = index_root / "opencode" / project_label / "events_index.manifest.json"
    atomic_write_json(manifest_path, manifest)
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize OpenCode raw records into canonical events")
    parser.add_argument("--mode", choices=["backfill", "incremental", "session"], default="incremental")
    parser.add_argument(
        "--project-worktree",
        default=detect_default_project_worktree(),
        help="Project worktree (defaults to git top-level)",
    )
    parser.add_argument("--raw-root", default="archive/raw/opencode", help="Root directory for raw session JSONL")
    parser.add_argument(
        "--events-root",
        default="archive/derived/events/opencode",
        help="Root directory for normalized event JSONL",
    )
    parser.add_argument(
        "--manifest-root",
        default="archive/manifests/opencode",
        help="Root directory for event manifests",
    )
    parser.add_argument("--index-root", default="archive/index", help="Root directory for event index artifacts")
    parser.add_argument(
        "--checkpoint-path",
        default="archive/checkpoints/opencode_events_state.json",
        help="Checkpoint path for incremental normalization",
    )
    parser.add_argument("--session-id", action="append", default=[], help="Session id for mode=session")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    worktree = str(Path(args.project_worktree).expanduser().resolve())
    project_label = Path(worktree).name

    raw_project_dir = Path(args.raw_root) / project_label
    events_project_dir = Path(args.events_root) / project_label
    manifest_project_dir = Path(args.manifest_root) / project_label
    checkpoint_path = Path(args.checkpoint_path)
    index_root = Path(args.index_root)

    if not raw_project_dir.exists():
        print(f"ERROR: Raw project directory not found: {raw_project_dir}", file=sys.stderr)
        return 2

    raw_files = sorted(raw_project_dir.glob("session_*.jsonl"))
    if not raw_files:
        print("No raw session files found to normalize.")
        return 0

    session_files: dict[str, Path] = {}
    for path in raw_files:
        sid = parse_session_id_from_raw_path(path)
        if sid:
            session_files[sid] = path

    if args.mode == "session":
        if not args.session_id:
            print("ERROR: --mode session requires --session-id", file=sys.stderr)
            return 2
        missing = [sid for sid in args.session_id if sid not in session_files]
        if missing:
            print("ERROR: Missing raw files for session ids: " + ", ".join(missing), file=sys.stderr)
            return 2
        selected_ids = list(dict.fromkeys(args.session_id))
    else:
        selected_ids = sorted(session_files.keys())

    cp_state = load_checkpoint(checkpoint_path)
    cp_key = checkpoint_key(worktree, project_label)
    cp_entry = get_checkpoint_entry(cp_state, cp_key)
    prev_hashes = cp_entry.get("session_file_hashes", {}) if isinstance(cp_entry, dict) else {}

    candidate_ids = selected_ids
    current_hashes: dict[str, str] = {}
    if args.mode == "incremental":
        filtered: list[str] = []
        for sid in selected_ids:
            raw_hash = sha256_file(session_files[sid])
            current_hashes[sid] = raw_hash
            if prev_hashes.get(sid) != raw_hash:
                filtered.append(sid)
        candidate_ids = filtered

    if not candidate_ids:
        print("No changed sessions to normalize.")
        return 0

    processed = 0
    total_events = 0
    event_type_counts: Counter[str] = Counter()

    for sid in candidate_ids:
        raw_path = session_files[sid]
        raw_hash = current_hashes.get(sid) or sha256_file(raw_path)
        records = load_jsonl(raw_path)
        events = normalize_session_records(session_id=sid, project_label=project_label, records=records)

        for e in events:
            et = e.get("event_type")
            if isinstance(et, str):
                event_type_counts[et] += 1

        out_path = events_project_dir / f"session_{sid}.events.jsonl"
        manifest_path = manifest_project_dir / f"session_{sid}.events.manifest.json"

        if args.dry_run:
            print(f"DRY-RUN normalize session={sid} events={len(events)} -> {out_path}")
        else:
            atomic_write_jsonl(out_path, events)
            manifest = {
                "schema_version": 1,
                "event_schema_version": SCHEMA_VERSION,
                "normalizer_version": NORMALIZER_VERSION,
                "session_id": sid,
                "project_label": project_label,
                "source_raw_jsonl_path": str(raw_path),
                "source_raw_jsonl_sha256": raw_hash,
                "source_raw_record_count": len(records),
                "events_jsonl_path": str(out_path),
                "events_jsonl_sha256": sha256_file(out_path),
                "events_jsonl_bytes": out_path.stat().st_size,
                "event_count": len(events),
                "event_type_counts": dict(Counter(e["event_type"] for e in events)),
                "updated_at": utc_now_iso(),
            }
            atomic_write_json(manifest_path, manifest)
            if args.verbose:
                print(f"UPDATED session={sid} events={len(events)} -> {out_path}")

        processed += 1
        total_events += len(events)
        current_hashes[sid] = raw_hash

    if not args.dry_run:
        merged_hashes = dict(prev_hashes) if isinstance(prev_hashes, dict) else {}
        merged_hashes.update(current_hashes)
        put_checkpoint_entry(cp_state, cp_key, merged_hashes)
        atomic_write_json(checkpoint_path, cp_state)
        index_path = write_events_index(index_root=index_root, project_label=project_label, source_root=Path(args.events_root))
        print(f"Events index updated: {index_path}")

    print(
        "Done. "
        f"mode={args.mode} project={project_label} sessions={processed} events={total_events} "
        f"event_types={dict(event_type_counts)} dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
