# GitHub Issues Task Tracking

This document is the canonical task-state model for Architect/Executor/Reviewer workflow.

## Source of truth

- Task state lives in GitHub Issue labels, not repo-local YAML files.
- Every active task issue must include one `ExecPlan Path` value pointing to `agents/plans/<task-slug>.md`.

## Canonical labels

Task state labels (exactly one at a time):

- `task:ready`
- `task:in_progress`
- `task:blocked`
- `task:ready_for_review`
- `task:review_in_progress`
- `task:done`

Owner labels (exactly one at a time):

- `role:architect`
- `role:executor`
- `role:reviewer`

Support labels:

- `kind:migration`

## Transition model

1. Architect creates/plans issue and sets `task:ready` + `role:executor`.
2. Executor starts work and sets `task:in_progress` + `role:executor`.
3. Executor opens PR, links it in issue + ExecPlan, then sets `task:ready_for_review` + `role:reviewer`.
4. Reviewer starts review and sets `task:review_in_progress` + `role:reviewer`.
5. Reviewer either:
   - Requests changes: set `task:in_progress` + `role:executor`.
   - Merges PR: set `task:done` + `role:architect`.
6. If blocked at any phase: set `task:blocked` and capture blocker details in issue + ExecPlan.

## Feedback protocol

- Agents leave feedback as PR/Issue comments, not formal "request changes" review actions.
- Every feedback comment must start with role prefix format: `[<role>] <comments>`.
- Canonical role prefixes: `[architect]`, `[executor]`, `[reviewer]`.
- When requesting rework, include explicit required changes and expected state-label transition in the same comment.

## Query examples

Run from repo root:

```bash
gh issue list --state open --label task:ready
gh issue list --state open --label task:in_progress
gh issue list --state open --label task:ready_for_review
gh issue list --state open --label task:review_in_progress
gh issue list --state open --label task:blocked
```

## Legacy note

- `agents/context/tasks.yaml` and `agents/scripts/lint_tasks_state.py` are archived/deprecated and are not part of active workflow.
