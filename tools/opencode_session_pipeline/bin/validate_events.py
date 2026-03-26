#!/usr/bin/env python3
"""Validate normalized event coverage against raw session archives."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ALLOWED_EVENT_TYPES = {
    "session_started",
    "session_archived",
    "user_turn",
    "assistant_turn",
    "message_observed",
    "artifact_batch_changed",
    "tool_execution",
    "tool_failure",
    "validation_result",
    "todo_state_changed",
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def parse_session_id_from_raw(path: Path) -> str | None:
    name = path.name
    if not name.startswith("session_") or not name.endswith(".jsonl"):
        return None
    return name[len("session_") : -len(".jsonl")]


def parse_session_id_from_events(path: Path) -> str | None:
    name = path.name
    if not name.startswith("session_") or not name.endswith(".events.jsonl"):
        return None
    return name[len("session_") : -len(".events.jsonl")]


def parse_message_role(record: dict[str, Any]) -> str | None:
    payload = record.get("payload_raw")
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, str):
        return None
    try:
        obj = json.loads(data)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    role = obj.get("role")
    return role if isinstance(role, str) else None


def validate_session(raw_rows: list[dict[str, Any]], event_rows: list[dict[str, Any]]) -> dict[str, Any]:
    raw_type_counts: Counter[str] = Counter()
    raw_message_roles: Counter[str] = Counter()
    tool_part_count = 0
    todo_count = 0
    for row in raw_rows:
        rt = row.get("record_type")
        if isinstance(rt, str):
            raw_type_counts[rt] += 1
        if rt == "message":
            role = parse_message_role(row)
            if role:
                raw_message_roles[role] += 1
        if rt == "part":
            payload = row.get("payload_raw")
            data = payload.get("data") if isinstance(payload, dict) else None
            if isinstance(data, str):
                try:
                    obj = json.loads(data)
                except Exception:
                    obj = None
                if isinstance(obj, dict) and obj.get("type") == "tool":
                    tool_part_count += 1
        if rt == "todo":
            todo_count += 1

    event_type_counts: Counter[str] = Counter()
    invalid_event_types: Counter[str] = Counter()
    missing_provenance = 0
    for e in event_rows:
        et = e.get("event_type")
        if isinstance(et, str):
            event_type_counts[et] += 1
            if et not in ALLOWED_EVENT_TYPES:
                invalid_event_types[et] += 1
        prov = e.get("provenance")
        if not isinstance(prov, dict) or not prov.get("record_fingerprint"):
            missing_provenance += 1

    user_turns = event_type_counts.get("user_turn", 0)
    assistant_turns = event_type_counts.get("assistant_turn", 0)
    tool_execs = event_type_counts.get("tool_execution", 0)
    todo_changes = event_type_counts.get("todo_state_changed", 0)
    session_started = event_type_counts.get("session_started", 0)

    checks = {
        "has_session_started": session_started >= 1,
        "user_turn_coverage_ok": user_turns <= raw_message_roles.get("user", 0),
        "assistant_turn_coverage_ok": assistant_turns <= raw_message_roles.get("assistant", 0),
        "tool_execution_coverage_ok": tool_execs <= tool_part_count,
        "todo_change_coverage_ok": todo_changes <= todo_count,
        "all_events_have_provenance": missing_provenance == 0,
        "event_types_valid": len(invalid_event_types) == 0,
    }

    return {
        "raw_record_count": len(raw_rows),
        "event_count": len(event_rows),
        "raw_record_type_counts": dict(raw_type_counts),
        "raw_message_role_counts": dict(raw_message_roles),
        "event_type_counts": dict(event_type_counts),
        "invalid_event_types": dict(invalid_event_types),
        "missing_provenance_count": missing_provenance,
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate normalized OpenCode events")
    p.add_argument("--project", default="", help="Project label; defaults to current directory name")
    p.add_argument("--raw-root", default="archive/raw/opencode", help="Raw root directory")
    p.add_argument("--events-root", default="archive/derived/events/opencode", help="Events root directory")
    p.add_argument("--index-root", default="archive/index", help="Index/report root directory")
    p.add_argument("--session-id", action="append", default=[], help="Validate only selected session ids")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    project = args.project or Path.cwd().resolve().name
    raw_dir = Path(args.raw_root) / project
    events_dir = Path(args.events_root) / project
    index_dir = Path(args.index_root) / "opencode" / project

    if not raw_dir.exists():
        print(f"ERROR: raw directory not found: {raw_dir}")
        return 2
    if not events_dir.exists():
        print(f"ERROR: events directory not found: {events_dir}")
        return 2

    raw_files = {parse_session_id_from_raw(p): p for p in raw_dir.glob("session_*.jsonl")}
    raw_files = {k: v for k, v in raw_files.items() if k}
    event_files = {parse_session_id_from_events(p): p for p in events_dir.glob("session_*.events.jsonl")}
    event_files = {k: v for k, v in event_files.items() if k}

    if args.session_id:
        target_ids = list(dict.fromkeys(args.session_id))
    else:
        target_ids = sorted(set(raw_files.keys()) | set(event_files.keys()))

    sessions: dict[str, Any] = {}
    missing_events: list[str] = []
    missing_raw: list[str] = []
    ok_count = 0
    fail_count = 0

    for sid in target_ids:
        raw_path = raw_files.get(sid)
        ev_path = event_files.get(sid)
        if raw_path is None:
            missing_raw.append(sid)
            continue
        if ev_path is None:
            missing_events.append(sid)
            continue

        raw_rows = load_jsonl(raw_path)
        event_rows = load_jsonl(ev_path)
        session_result = validate_session(raw_rows, event_rows)
        checks = session_result.get("checks", {})
        passed = all(bool(v) for v in checks.values())
        if passed:
            ok_count += 1
        else:
            fail_count += 1
        sessions[sid] = session_result

    report = {
        "generated_at": utc_now_iso(),
        "project": project,
        "summary": {
            "sessions_checked": len(sessions),
            "sessions_ok": ok_count,
            "sessions_failed": fail_count,
            "missing_events": len(missing_events),
            "missing_raw": len(missing_raw),
        },
        "missing_events": missing_events,
        "missing_raw": missing_raw,
        "sessions": sessions,
    }

    index_dir.mkdir(parents=True, exist_ok=True)
    report_path = index_dir / "events_validation.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, ensure_ascii=True)
        f.write("\n")

    print(
        "Validation complete. "
        f"project={project} checked={len(sessions)} ok={ok_count} failed={fail_count} "
        f"missing_events={len(missing_events)} missing_raw={len(missing_raw)} report={report_path}"
    )
    return 0 if (fail_count == 0 and not missing_events and not missing_raw) else 1


if __name__ == "__main__":
    raise SystemExit(main())
