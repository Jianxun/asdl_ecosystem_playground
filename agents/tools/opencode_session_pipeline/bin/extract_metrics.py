#!/usr/bin/env python3
"""Extract evaluator-friendly metrics from OpenCode session artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def event_path(events_root: Path, project: str, session_id: str) -> Path:
    return events_root / project / f"session_{session_id}.events.jsonl"


def raw_path(raw_root: Path, project: str, session_id: str) -> Path:
    return raw_root / project / f"session_{session_id}.jsonl"


def safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def extract_token_snapshot(raw_rows: list[dict[str, Any]]) -> dict[str, Any]:
    snapshots: list[dict[str, Any]] = []
    for row in raw_rows:
        if row.get("record_type") != "part":
            continue
        payload_raw = row.get("payload_raw") if isinstance(row.get("payload_raw"), dict) else {}
        data = payload_raw.get("data")
        if not isinstance(data, str):
            continue
        try:
            obj = json.loads(data)
        except Exception:
            continue
        if not isinstance(obj, dict) or obj.get("type") != "step-finish":
            continue
        tok = obj.get("tokens") if isinstance(obj.get("tokens"), dict) else {}
        cache = tok.get("cache") if isinstance(tok.get("cache"), dict) else {}
        snapshots.append(
            {
                "reason": obj.get("reason"),
                "time_created": safe_int(row.get("time_created")),
                "total": safe_int(tok.get("total")) or 0,
                "input": safe_int(tok.get("input")) or 0,
                "output": safe_int(tok.get("output")) or 0,
                "reasoning": safe_int(tok.get("reasoning")) or 0,
                "cache_read": safe_int(cache.get("read")) or 0,
                "cache_write": safe_int(cache.get("write")) or 0,
                "cost": obj.get("cost"),
            }
        )

    if not snapshots:
        return {
            "method": "missing",
            "tokens_total": None,
            "tokens_input": None,
            "tokens_output": None,
            "tokens_reasoning": None,
            "cache_read": None,
            "cache_write": None,
            "cost": None,
        }

    stop = [s for s in snapshots if s.get("reason") == "stop"]
    if stop:
        chosen = sorted(stop, key=lambda s: (s.get("time_created") or -1, s.get("total") or -1))[-1]
        method = "final_stop_snapshot"
    else:
        chosen = sorted(snapshots, key=lambda s: (s.get("total") or -1, s.get("time_created") or -1))[-1]
        method = "max_total_snapshot"

    return {
        "method": method,
        "tokens_total": chosen.get("total"),
        "tokens_input": chosen.get("input"),
        "tokens_output": chosen.get("output"),
        "tokens_reasoning": chosen.get("reasoning"),
        "cache_read": chosen.get("cache_read"),
        "cache_write": chosen.get("cache_write"),
        "cost": chosen.get("cost"),
    }


def compute_metrics(events_rows: list[dict[str, Any]], raw_rows: list[dict[str, Any]]) -> dict[str, Any]:
    session_start = None
    session_end = None

    tool_execution_count = 0
    tool_failure_count = 0
    bash_count = 0
    long_cmd_ge_120 = 0
    long_cmd_ge_200 = 0
    compound_cmd_count = 0
    max_command_len = 0

    for event in events_rows:
        et = event.get("event_type")
        t = safe_int(event.get("event_time"))
        if t is not None:
            if session_start is None or t < session_start:
                session_start = t
            if session_end is None or t > session_end:
                session_end = t

        if et == "tool_execution":
            tool_execution_count += 1
            payload = event.get("payload_compact") if isinstance(event.get("payload_compact"), dict) else {}
            tool = payload.get("tool")
            inp = payload.get("input") if isinstance(payload.get("input"), dict) else {}
            cmd_len = safe_int(inp.get("command_len")) or 0
            chain_count = safe_int(inp.get("chain_count")) or 0

            if tool == "bash":
                bash_count += 1
                if cmd_len >= 120:
                    long_cmd_ge_120 += 1
                if cmd_len >= 200:
                    long_cmd_ge_200 += 1
                if chain_count > 1:
                    compound_cmd_count += 1
                if cmd_len > max_command_len:
                    max_command_len = cmd_len

        elif et == "tool_failure":
            tool_failure_count += 1

    wall_clock_sec = None
    if session_start is not None and session_end is not None and session_end >= session_start:
        wall_clock_sec = round((session_end - session_start) / 1000.0, 3)

    token_metrics = extract_token_snapshot(raw_rows)

    return {
        "wall_clock_sec": wall_clock_sec,
        "tool_execution_count": tool_execution_count,
        "tool_failure_count": tool_failure_count,
        "bash_count": bash_count,
        "long_cmd_ge_120": long_cmd_ge_120,
        "long_cmd_ge_200": long_cmd_ge_200,
        "compound_cmd_count": compound_cmd_count,
        "max_command_len": max_command_len,
        **token_metrics,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract evaluator metrics for OpenCode session(s)")
    p.add_argument("--project", default=Path.cwd().resolve().name, help="Project label")
    p.add_argument("--events-root", default="archive/derived/events/opencode", help="Events root")
    p.add_argument("--raw-root", default="archive/raw/opencode", help="Raw root")
    p.add_argument("--session-id", action="append", default=[], help="Target session id (repeatable)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.session_id:
        raise SystemExit("ERROR: provide at least one --session-id")

    events_root = Path(args.events_root)
    raw_root = Path(args.raw_root)

    out: list[dict[str, Any]] = []
    for sid in args.session_id:
        epath = event_path(events_root, args.project, sid)
        rpath = raw_path(raw_root, args.project, sid)
        if not epath.exists():
            raise SystemExit(f"ERROR: events file not found: {epath}")
        if not rpath.exists():
            raise SystemExit(f"ERROR: raw file not found: {rpath}")

        events_rows = load_jsonl(epath)
        raw_rows = load_jsonl(rpath)
        metrics = compute_metrics(events_rows, raw_rows)
        out.append(
            {
                "project": args.project,
                "session_id": sid,
                "metrics": metrics,
                "evidence": {
                    "events_path": str(epath),
                    "raw_path": str(rpath),
                },
            }
        )

    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=True, sort_keys=True))
    else:
        for row in out:
            print(json.dumps(row, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
