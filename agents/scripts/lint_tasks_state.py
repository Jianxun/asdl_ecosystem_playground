#!/usr/bin/env python3
"""Lint task metadata and runtime state in consolidated tasks.yaml."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


TASK_ID_RE = re.compile(r"^T-\d{3}$")
ALLOWED_STATUSES = {
    "backlog",
    "ready",
    "in_progress",
    "blocked",
    "ready_for_review",
    "review_in_progress",
    "review_clean",
    "request_changes",
    "escalation_needed",
    "done",
}
EARLY_STATUSES = {"backlog", "ready", "blocked"}
REVIEW_STATUSES = {
    "ready_for_review",
    "review_in_progress",
    "review_clean",
    "request_changes",
    "escalation_needed",
}
TASK_REQUIRED_KEYS = {"id", "title", "status", "pr", "merged", "execplan"}
TASK_ALLOWED_KEYS = TASK_REQUIRED_KEYS | {"owner", "depends_on"}
LEGACY_TASK_KEYS = {"dod", "verify", "files", "links"}


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping at the top level.")
    return data


def lint_task_entry(task: dict, label: str, index: int, errors: list[str]) -> tuple[str | None, list[str]]:
    task_id = task.get("id")
    if not isinstance(task_id, str):
        errors.append(f"{label}[{index}].id must be a string.")
        return None, []

    if not TASK_ID_RE.match(task_id):
        errors.append(f"{label}[{index}].id '{task_id}' must match T-000 format.")

    missing_keys = TASK_REQUIRED_KEYS - set(task.keys())
    if missing_keys:
        errors.append(
            f"{label}[{index}] is missing keys: {', '.join(sorted(missing_keys))}."
        )

    extra_keys = set(task.keys()) - TASK_ALLOWED_KEYS
    if extra_keys:
        errors.append(
            f"{label}[{index}] has unexpected keys: {', '.join(sorted(extra_keys))}."
        )

    legacy_keys = set(task.keys()) & LEGACY_TASK_KEYS
    if legacy_keys:
        errors.append(
            f"{label}[{index}] includes retired keys: {', '.join(sorted(legacy_keys))}."
        )

    depends_on = task.get("depends_on")
    deps: list[str] = []
    if depends_on is not None:
        if not isinstance(depends_on, list):
            errors.append(f"{label}[{index}].depends_on must be a list.")
        else:
            seen_deps: set[str] = set()
            for dep in depends_on:
                if not isinstance(dep, str):
                    errors.append(f"{label}[{index}].depends_on values must be strings.")
                    continue
                if not TASK_ID_RE.match(dep):
                    errors.append(
                        f"{label}[{index}].depends_on '{dep}' must match T-000 format."
                    )
                if dep in seen_deps:
                    errors.append(
                        f"{label}[{index}].depends_on contains duplicate '{dep}'."
                    )
                    continue
                seen_deps.add(dep)
                deps.append(dep)
            if task_id in seen_deps:
                errors.append(f"{label}[{index}].depends_on cannot include itself.")

    status = task.get("status")
    pr_value = task.get("pr")
    merged_value = task.get("merged")
    execplan = task.get("execplan")

    if not isinstance(execplan, str) or not execplan.strip():
        errors.append(f"{label}[{index}].execplan for '{task_id}' must be a non-empty string.")

    if not isinstance(status, str):
        errors.append(f"{label}[{index}].status for '{task_id}' must be a string.")
    elif status not in ALLOWED_STATUSES:
        errors.append(f"{label}[{index}].status '{status}' for '{task_id}' is invalid.")

    if pr_value is None:
        pr_is_set = False
    elif isinstance(pr_value, int):
        if pr_value < 0:
            errors.append(
                f"{label}[{index}].pr for '{task_id}' must be a non-negative integer."
            )
        pr_is_set = pr_value > 0
    else:
        errors.append(
            f"{label}[{index}].pr for '{task_id}' must be null or a non-negative integer."
        )
        pr_is_set = False

    if not isinstance(merged_value, bool):
        errors.append(f"{label}[{index}].merged for '{task_id}' must be a boolean.")

    if isinstance(status, str) and status in EARLY_STATUSES:
        if pr_value is not None:
            errors.append(f"{label}[{index}].pr for '{task_id}' must be null in '{status}'.")
        if merged_value is not False:
            errors.append(
                f"{label}[{index}].merged for '{task_id}' must be false in '{status}'."
            )
    if isinstance(status, str) and status == "in_progress":
        if pr_value is not None and not pr_is_set:
            errors.append(
                f"{label}[{index}].pr for '{task_id}' must be a positive integer in '{status}'."
            )
        if merged_value is not False:
            errors.append(
                f"{label}[{index}].merged for '{task_id}' must be false in '{status}'."
            )
    if isinstance(status, str) and status in REVIEW_STATUSES:
        if not pr_is_set:
            errors.append(
                f"{label}[{index}].pr for '{task_id}' must be a positive integer in '{status}'."
            )
        if merged_value is not False:
            errors.append(
                f"{label}[{index}].merged for '{task_id}' must be false in '{status}'."
            )
    if isinstance(status, str) and status == "done":
        if not pr_is_set:
            errors.append(
                f"{label}[{index}].pr for '{task_id}' must be a positive integer in 'done'."
            )
        if merged_value is not True:
            errors.append(
                f"{label}[{index}].merged for '{task_id}' must be true in 'done'."
            )

    return task_id, deps


def collect_tasks(tasks: list, label: str, errors: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    ids: list[str] = []
    dependencies: dict[str, list[str]] = {}
    if not isinstance(tasks, list):
        errors.append(f"{label} must be a list.")
        return ids, dependencies

    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"{label}[{index}] must be a mapping.")
            continue
        task_id, deps = lint_task_entry(task, label, index, errors)
        if task_id is None:
            continue
        ids.append(task_id)
        dependencies[task_id] = deps
    return ids, dependencies


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    tasks_path = repo_root / "agents/context/tasks.yaml"
    errors: list[str] = []

    try:
        tasks_data = load_yaml(tasks_path)
    except Exception as exc:  # noqa: BLE001 - keep CLI output simple
        print(f"ERROR: {exc}")
        return 1

    if tasks_data.get("schema_version") != 3:
        errors.append(f"{tasks_path} schema_version must be 3.")

    current_sprint = tasks_data.get("current_sprint", [])
    backlog = tasks_data.get("backlog", [])
    current_ids, current_deps = collect_tasks(current_sprint, "current_sprint", errors)
    backlog_ids, backlog_deps = collect_tasks(backlog, "backlog", errors)
    active_ids = current_ids + backlog_ids
    active_deps = {**current_deps, **backlog_deps}

    seen_ids: set[str] = set()
    for task_id in active_ids:
        if task_id in seen_ids:
            errors.append(f"Duplicate task id '{task_id}' in tasks.yaml.")
        seen_ids.add(task_id)

    for task_id, deps in active_deps.items():
        for dep in deps:
            if dep not in seen_ids:
                errors.append(
                    f"tasks.yaml task '{task_id}' depends_on inactive or missing task '{dep}'."
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("OK: tasks.yaml metadata and status fields are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
