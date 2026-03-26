#!/usr/bin/env python3
"""Run `opencode run` with optional GitHub Issue scheduling."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time
from typing import Any, Iterable, TextIO

DEFAULT_PROMPT = "analyze the structure of the codebase"
MAX_REVIEW_ROUNDS = 3
IMESSAGE_SCRIPT = os.path.join(os.path.dirname(__file__), "send_imessage.sh")
LOGS_DIR = Path("agents/log")
WORKTREES_REL = Path("agents/worktrees")

TASK_LABELS = {
    "task:ready",
    "task:in_progress",
    "task:blocked",
    "task:ready_for_review",
    "task:review_in_progress",
    "task:done",
}

ROLE_LABELS = {
    "role:architect",
    "role:executor",
    "role:reviewer",
}

ANSI_GREEN = "\033[32m"
ANSI_BLUE = "\033[34m"
ANSI_RESET = "\033[0m"


def build_command(prompt: str) -> list[str]:
    return ["opencode", "run", "--format", "json", prompt]


def format_event(payload: dict[str, Any]) -> tuple[str, str]:
    event_type = payload.get("type", "unknown")
    if event_type == "step_start":
        return "[step.start]", "default"
    if event_type == "step_finish":
        part = payload.get("part", {})
        reason = part.get("reason") if isinstance(part, dict) else None
        return f"[step.done] reason={reason}", "default"
    if event_type == "text":
        part = payload.get("part", {})
        text = (part.get("text") if isinstance(part, dict) else "") or ""
        text = text.strip()
        return (f"[agent] {text}", "agent") if text else ("[agent]", "agent")
    if event_type == "item.started":
        item = payload.get("item", {})
        item_type = item.get("type", "unknown")
        cmd = item.get("command")
        if item_type == "command_execution" and cmd:
            return f"[command.start] {cmd}", "default"
        return f"[item.start] {item_type}", "default"
    if event_type == "item.completed":
        item = payload.get("item", {})
        item_type = item.get("type", "unknown")
        if item_type == "command_execution":
            exit_code = item.get("exit_code")
            return f"[command.done] exit={exit_code}", "default"
        if item_type == "reasoning":
            text = (item.get("text") or "").strip()
            return (f"[reasoning] {text}", "reasoning") if text else ("[reasoning]", "reasoning")
        if item_type == "agent_message":
            text = (item.get("text") or "").strip()
            return (f"[agent] {text}", "agent") if text else ("[agent]", "agent")
        return f"[item.done] {item_type}", "default"
    if event_type == "turn.completed":
        usage = payload.get("usage", {})
        return (
            f"[turn.done] input_tokens={usage.get('input_tokens')} output_tokens={usage.get('output_tokens')}",
            "default",
        )
    return f"[event] {event_type}", "default"


def colorize(text: str, tag: str) -> str:
    if tag == "agent":
        return f"{ANSI_GREEN}{text}{ANSI_RESET}"
    if tag == "reasoning":
        return f"{ANSI_BLUE}{text}{ANSI_RESET}"
    return text


def render_line(line: str) -> tuple[str, str, str | None, dict[str, Any] | None]:
    stripped = line.strip()
    if not stripped:
        return "", "default", None, None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped, "default", None, None

    formatted, tag = format_event(payload)
    agent_text: str | None = None
    if payload.get("type") == "text":
        part = payload.get("part", {})
        if isinstance(part, dict):
            agent_text = (part.get("text") or "").strip() or None
    if payload.get("type") == "item.completed":
        item = payload.get("item", {})
        if item.get("type") == "agent_message":
            agent_text = (item.get("text") or "").strip()
    return formatted, tag, agent_text, payload


def open_task_log(issue_id: str, role: str, command: Iterable[str], cwd: str | None) -> tuple[TextIO, str]:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = LOGS_DIR / f"issue-{issue_id}.log.json"
    handle = path.open("a", encoding="utf-8")
    session_id = f"issue-{issue_id}-{role}-{int(time.time() * 1000)}"
    handle.write(
        json.dumps(
            {
                "kind": "session_start",
                "session_id": session_id,
                "issue_id": issue_id,
                "role": role,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "command": list(command),
                "cwd": cwd or os.getcwd(),
            },
            ensure_ascii=True,
        )
        + "\n"
    )
    handle.flush()
    return handle, session_id


def write_log_event(
    handle: TextIO,
    session_id: str,
    stream: str,
    raw_line: str,
    formatted: str,
    tag: str,
    payload: dict[str, Any] | None,
) -> None:
    event = {
        "kind": "event",
        "session_id": session_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stream": stream,
        "raw": raw_line.rstrip("\n"),
        "formatted": formatted,
        "tag": tag,
        "payload": payload,
    }
    handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def close_task_log(handle: TextIO, session_id: str, exit_code: int, summary: str | None) -> None:
    handle.write(
        json.dumps(
            {
                "kind": "session_end",
                "session_id": session_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "exit_code": exit_code,
                "last_agent_message": summary,
            },
            ensure_ascii=True,
        )
        + "\n"
    )
    handle.flush()
    handle.close()


def stream_process(
    command: Iterable[str],
    prefix: str | None = None,
    issue_id: str | None = None,
    role: str | None = None,
    cwd: str | None = None,
) -> tuple[int, str | None]:
    last_agent_message: str | None = None
    log_handle: TextIO | None = None
    session_id: str | None = None
    command_list = list(command)

    if issue_id and role:
        log_handle, session_id = open_task_log(issue_id, role, command_list, cwd)

    try:
        proc = subprocess.Popen(
            command_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=cwd,
        )
    except FileNotFoundError as exc:
        print(f"Required binary not found: {exc}. Ensure opencode is installed.", file=sys.stderr)
        if log_handle is not None and session_id is not None:
            close_task_log(log_handle, session_id, 127, None)
        return 127, None

    selector = selectors.DefaultSelector()
    if proc.stdout is not None:
        selector.register(proc.stdout, selectors.EVENT_READ, data="stdout")
    if proc.stderr is not None:
        selector.register(proc.stderr, selectors.EVENT_READ, data="stderr")

    while selector.get_map():
        for key, _ in selector.select():
            file_obj = key.fileobj
            readline = getattr(file_obj, "readline", None)
            if readline is None:
                selector.unregister(file_obj)
                continue
            line = readline()
            if line == "":
                selector.unregister(file_obj)
                continue
            formatted, tag, agent_text, payload = render_line(line)
            if not formatted:
                continue
            if agent_text:
                last_agent_message = agent_text

            if log_handle is not None and session_id is not None:
                write_log_event(
                    log_handle,
                    session_id,
                    str(key.data),
                    line,
                    formatted,
                    tag,
                    payload,
                )

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            output = f"[{timestamp}] {colorize(formatted, tag)}\n"
            if prefix:
                output = f"{prefix} {output}"
            if key.data == "stderr":
                sys.stderr.write(output)
                sys.stderr.flush()
            else:
                sys.stdout.write(output)
                sys.stdout.flush()

    exit_code = proc.wait()
    if log_handle is not None and session_id is not None:
        close_task_log(log_handle, session_id, exit_code, last_agent_message)
    return exit_code, last_agent_message


def run_gh_json(args: list[str]) -> Any:
    proc = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(proc.stdout)


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(proc.stdout.strip()).resolve()


def ensure_issue_worktree(issue_number: int) -> Path:
    root = repo_root()
    worktree_root = root / WORKTREES_REL
    worktree_path = worktree_root / f"issue-{issue_number}"
    if worktree_path.exists():
        return worktree_path

    worktree_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "worktree", "add", str(worktree_path), "main"], check=True, cwd=str(root))
    return worktree_path


def issue_info(issue_number: int) -> dict[str, Any]:
    return run_gh_json(["issue", "view", str(issue_number), "--json", "number,title,body,labels,url"])


def issue_labels(issue_number: int) -> set[str]:
    info = issue_info(issue_number)
    labels = info.get("labels", [])
    return {item.get("name", "") for item in labels if isinstance(item, dict)}


def extract_execplan_path(issue_body: str) -> str | None:
    match = re.search(r"^### ExecPlan Path\n+(.+)$", issue_body, flags=re.MULTILINE)
    if not match:
        return None
    path = match.group(1).strip()
    return path if path else None


def list_ready_issues() -> list[int]:
    proc = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--state",
            "open",
            "--label",
            "task:ready",
            "--json",
            "number",
            "--jq",
            ".[].number",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    out = proc.stdout.strip()
    if not out:
        return []
    return [int(x) for x in out.splitlines() if x.strip()]


def build_executor_prompt(issue_number: int, repo_path: str, feedback: str | None = None) -> str:
    info = issue_info(issue_number)
    plan_path = extract_execplan_path(info.get("body", "")) or "<missing ExecPlan Path in issue body>"
    base = (
        "You are the executor agent. Read and follow your role definition "
        "'agents/roles/executor.md'. "
        f"Work on GitHub issue #{issue_number}. Execute plan '{plan_path}'. "
        f"Issue URL: {info.get('url')}. Repo path: {repo_path}."
    )
    if feedback:
        base = f"{base}\nReviewer feedback:\n{feedback}"
    return base


def build_reviewer_prompt(issue_number: int, repo_path: str, summary: str | None) -> str:
    info = issue_info(issue_number)
    plan_path = extract_execplan_path(info.get("body", "")) or "<missing ExecPlan Path in issue body>"
    summary_text = summary or "No executor summary captured."
    return (
        "You are the reviewer agent. Read and follow your role definition "
        "'agents/roles/reviewer.md'. "
        f"Review GitHub issue #{issue_number}. Use plan '{plan_path}'. "
        f"Issue URL: {info.get('url')}. Repo path: {repo_path}.\n"
        "Here are the summaries from the executor agent:\n"
        f"{summary_text}"
    )


def run_codex(
    prompt: str,
    issue_id: str | None = None,
    role: str | None = None,
    cwd: str | None = None,
) -> tuple[int, str | None]:
    command = build_command(prompt)
    print(f"Running: {' '.join(command)}")
    prefix = None
    if issue_id and role:
        prefix = f"[issue-{issue_id}][{role}]"
    return stream_process(command, prefix=prefix, issue_id=issue_id, role=role, cwd=cwd)


def send_imessage(role: str, issue_number: int, labels: set[str], response: str | None) -> None:
    label_text = ",".join(sorted(labels)) or "unknown"
    response_text = response or "No agent response captured."
    payload = f"[{role}] [issue-{issue_number}] ({label_text}): {response_text}"
    try:
        subprocess.run([IMESSAGE_SCRIPT, payload], check=False, text=True, capture_output=True)
    except FileNotFoundError:
        print(f"Warning: {IMESSAGE_SCRIPT} not found; skipping iMessage send.", file=sys.stderr)


def run_scheduler(issue_numbers: list[int], max_rounds: int) -> int:
    for issue_number in issue_numbers:
        print(f"Starting issue #{issue_number}")
        issue_worktree = ensure_issue_worktree(issue_number)
        issue_cwd = str(issue_worktree)
        print(f"Using worktree: {issue_cwd}")
        rounds = 0
        reviewer_feedback: str | None = None
        while rounds < max_rounds:
            executor_prompt = build_executor_prompt(issue_number, repo_path=issue_cwd, feedback=reviewer_feedback)
            exit_code, executor_summary = run_codex(
                executor_prompt,
                issue_id=str(issue_number),
                role="executor",
                cwd=issue_cwd,
            )
            if exit_code != 0:
                print(f"Interrupted: executor exited with code {exit_code}", file=sys.stderr)
                return exit_code

            labels = issue_labels(issue_number)
            send_imessage("executor", issue_number, labels, executor_summary)
            if "task:ready_for_review" not in labels:
                print(
                    f"Interrupted: issue #{issue_number} labels are {sorted(labels)}, expected task:ready_for_review.",
                    file=sys.stderr,
                )
                return 1

            reviewer_prompt = build_reviewer_prompt(issue_number, repo_path=issue_cwd, summary=executor_summary)
            exit_code, reviewer_summary = run_codex(
                reviewer_prompt,
                issue_id=str(issue_number),
                role="reviewer",
                cwd=issue_cwd,
            )
            if exit_code != 0:
                print(f"Interrupted: reviewer exited with code {exit_code}", file=sys.stderr)
                return exit_code

            labels = issue_labels(issue_number)
            send_imessage("reviewer", issue_number, labels, reviewer_summary)
            if "task:done" in labels:
                print(f"Issue #{issue_number} completed.")
                break
            if "task:in_progress" in labels:
                rounds += 1
                if rounds >= max_rounds:
                    print(
                        f"Interrupted: issue #{issue_number} exceeded {max_rounds} review rounds.",
                        file=sys.stderr,
                    )
                    return 1
                reviewer_feedback = reviewer_summary or "No reviewer summary captured."
                print(f"Issue #{issue_number} requested changes; restarting executor.")
                continue

            print(
                f"Interrupted: issue #{issue_number} labels are {sorted(labels)}, expected task:done or task:in_progress.",
                file=sys.stderr,
            )
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch opencode run in JSON mode and print events.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Prompt to pass to opencode run.")
    parser.add_argument("--issues", nargs="*", type=int, help="GitHub issue numbers to run in order.")
    parser.add_argument(
        "--all-ready",
        action="store_true",
        help="Run all open issues labeled task:ready (in GitHub list order).",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=MAX_REVIEW_ROUNDS,
        help="Maximum executor-reviewer rounds per issue.",
    )
    args = parser.parse_args()

    if args.all_ready and args.issues:
        print("Error: Use --all-ready or --issues, not both.", file=sys.stderr)
        return 2

    if args.all_ready or args.issues:
        issue_numbers = list(args.issues or [])
        if args.all_ready:
            issue_numbers = list_ready_issues()
        if not issue_numbers:
            print("No issues to run.")
            return 0
        return run_scheduler(issue_numbers, args.max_rounds)

    exit_code, _ = run_codex(args.prompt)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
