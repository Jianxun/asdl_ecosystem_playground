#!/usr/bin/env python3
"""Simple entry point to launch planner/executor/evaluator agents via opencode run.

Designed for cron/orchestrator use: one invocation -> one agent run.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROLE_MAP = {
    "planner": "architect",
    "architect": "architect",
    "executor": "executor",
    "evaluator": "evaluator",
    "reviewer": "reviewer",
}


def build_prompt(
    role: str,
    repo_path: Path,
    issue: int | None,
    session_ids: list[str],
    project: str,
    extra: str | None,
) -> str:
    mapped = ROLE_MAP[role]
    role_file = f"agents/roles/{mapped}.md"
    lines: list[str] = [
        f"You are the {mapped} agent.",
        f"Read and follow `{role_file}` strictly.",
        f"Repository root: {repo_path}",
    ]

    if issue is not None:
        lines.append(f"Target GitHub issue number: #{issue}.")

    if mapped == "evaluator":
        if session_ids:
            joined = ", ".join(session_ids)
            lines.append(f"Evaluate these explicit session IDs: {joined}.")
        lines.append(
            "Run ingestion + metrics extraction using repository tooling, then produce the evaluator report."
        )
        lines.append(f"Project label for telemetry commands: {project}.")

    if extra:
        lines.append("Additional instruction:")
        lines.append(extra)

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run one role agent via opencode run")
    p.add_argument(
        "--role",
        required=True,
        choices=sorted(ROLE_MAP.keys()),
        help="Agent role to run (planner maps to architect)",
    )
    p.add_argument("--issue", type=int, help="Optional GitHub issue number")
    p.add_argument(
        "--session-id",
        action="append",
        default=[],
        help="Evaluator target session id (repeatable)",
    )
    p.add_argument(
        "--project",
        default=Path.cwd().resolve().name,
        help="Telemetry project label (default: current directory name)",
    )
    p.add_argument("--repo-path", default=str(Path.cwd().resolve()), help="Repo root path")
    p.add_argument("--extra", help="Optional extra instruction appended to prompt")
    p.add_argument("--dry-run", action="store_true", help="Print prompt and exit")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_path = Path(args.repo_path).resolve()

    prompt = build_prompt(
        role=args.role,
        repo_path=repo_path,
        issue=args.issue,
        session_ids=list(args.session_id),
        project=args.project,
        extra=args.extra,
    )

    if args.dry_run:
        print(prompt)
        return 0

    cmd = ["opencode", "run", "--format", "json", prompt]
    try:
        proc = subprocess.run(cmd, cwd=str(repo_path))
    except FileNotFoundError:
        print("ERROR: 'opencode' binary not found in PATH.", file=sys.stderr)
        return 127

    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
