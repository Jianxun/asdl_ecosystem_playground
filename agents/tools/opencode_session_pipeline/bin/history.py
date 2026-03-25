#!/usr/bin/env python3
"""Query CLI for normalized OpenCode session event history."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def event_path(events_root: Path, project: str, session_id: str) -> Path:
    return events_root / project / f"session_{session_id}.events.jsonl"


def print_line(obj: dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=True, separators=(",", ":")))


def cmd_timeline(args: argparse.Namespace) -> int:
    path = event_path(Path(args.events_root), args.project, args.session_id)
    if not path.exists():
        print(f"ERROR: events file not found: {path}", file=sys.stderr)
        return 2
    rows = load_jsonl(path)
    if args.limit:
        rows = rows[: args.limit]
    for row in rows:
        print_line(
            {
                "seq": row.get("seq"),
                "event_time": row.get("event_time"),
                "event_type": row.get("event_type"),
                "actor_role": row.get("actor_role"),
                "status": row.get("status"),
                "event_id": row.get("event_id"),
            }
        )
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    path = event_path(Path(args.events_root), args.project, args.session_id)
    if not path.exists():
        print(f"ERROR: events file not found: {path}", file=sys.stderr)
        return 2
    rows = load_jsonl(path)
    for row in rows:
        et = row.get("event_type")
        if et not in {"tool_execution", "tool_failure", "validation_result"}:
            continue
        if args.failed_only and et != "tool_failure":
            continue
        payload = row.get("payload_compact") if isinstance(row.get("payload_compact"), dict) else {}
        print_line(
            {
                "seq": row.get("seq"),
                "event_time": row.get("event_time"),
                "event_type": et,
                "tool": payload.get("tool"),
                "call_id": payload.get("call_id") or payload.get("callID"),
                "status": row.get("status") or payload.get("status"),
                "exit_code": payload.get("exit_code"),
                "event_id": row.get("event_id"),
            }
        )
    return 0


def cmd_artifacts(args: argparse.Namespace) -> int:
    path = event_path(Path(args.events_root), args.project, args.session_id)
    if not path.exists():
        print(f"ERROR: events file not found: {path}", file=sys.stderr)
        return 2
    rows = load_jsonl(path)
    for row in rows:
        if row.get("event_type") != "artifact_batch_changed":
            continue
        payload = row.get("payload_compact") if isinstance(row.get("payload_compact"), dict) else {}
        print_line(
            {
                "seq": row.get("seq"),
                "event_time": row.get("event_time"),
                "message_id": payload.get("message_id"),
                "diff_count": payload.get("diff_count"),
                "diffs": payload.get("diffs"),
                "event_id": row.get("event_id"),
            }
        )
    return 0


def cmd_around(args: argparse.Namespace) -> int:
    events_base = Path(args.events_root) / args.project
    if not events_base.exists():
        print(f"ERROR: events project directory not found: {events_base}", file=sys.stderr)
        return 2

    target_rows: list[dict[str, Any]] = []
    for file in events_base.glob("session_*.events.jsonl"):
        rows = load_jsonl(file)
        for idx, row in enumerate(rows):
            if row.get("event_id") == args.event_id:
                start = max(0, idx - args.window)
                end = min(len(rows), idx + args.window + 1)
                target_rows = rows[start:end]
                break
        if target_rows:
            break

    if not target_rows:
        print(f"ERROR: event id not found: {args.event_id}", file=sys.stderr)
        return 2

    for row in target_rows:
        print_line(
            {
                "seq": row.get("seq"),
                "event_time": row.get("event_time"),
                "event_type": row.get("event_type"),
                "actor_role": row.get("actor_role"),
                "status": row.get("status"),
                "event_id": row.get("event_id"),
            }
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Session history query tool for OpenCode canonical events")
    p.add_argument("--project", default=Path.cwd().resolve().name, help="Project label")
    p.add_argument("--events-root", default="archive/derived/events/opencode", help="Events root")

    sub = p.add_subparsers(dest="command", required=True)

    t = sub.add_parser("timeline", help="Show timeline for a session")
    t.add_argument("--session-id", required=True)
    t.add_argument("--limit", type=int, default=0)
    t.set_defaults(func=cmd_timeline)

    tools = sub.add_parser("tools", help="Show tool-related events")
    tools.add_argument("--session-id", required=True)
    tools.add_argument("--failed-only", action="store_true")
    tools.set_defaults(func=cmd_tools)

    a = sub.add_parser("artifacts", help="Show artifact diff batch events")
    a.add_argument("--session-id", required=True)
    a.set_defaults(func=cmd_artifacts)

    around = sub.add_parser("around", help="Show event window around event id")
    around.add_argument("--event-id", required=True)
    around.add_argument("--window", type=int, default=5)
    around.set_defaults(func=cmd_around)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
