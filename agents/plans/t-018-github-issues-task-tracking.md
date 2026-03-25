# Migrate Task Tracking to GitHub Issues

## Purpose / Big Picture

Replace `agents/context/tasks.yaml` as the canonical task state machine with GitHub Issues so task lifecycle, ownership, review state, and history are managed in one collaborative system. Keep ExecPlans in-repo as execution artifacts, linked from issues.

This migration is intentionally a clean break. Temporary flow breakage is acceptable while role docs and scripts are updated.

## Progress

- [x] 2026-03-25 05:05Z Architect created migration ExecPlan for clean-break transition.
- [x] 2026-03-25 04:44Z Defined and applied GitHub Issue label/state model via `gh label create`/`gh label edit`.
- [x] 2026-03-25 04:53Z Updated role/workflow/context docs to remove active `tasks.yaml` dependency.
- [x] 2026-03-25 04:56Z Retired `tasks.yaml` state-machine files and rewired dispatcher for issue-based scheduling.
- [x] 2026-03-25 04:59Z Validated Architect -> Executor -> Reviewer lifecycle with pilot issue `#7`.

## Surprises & Discoveries

- Existing role files and lint scripts assume `tasks.yaml` is always present and authoritative.
- Current policy and tooling encode status constraints in `agents/scripts/lint_tasks_state.py`; this logic must move to operational conventions (labels/checklists) in GitHub.
- Historical plans/scratchpads still mention `tasks.yaml`, so acceptance checks must distinguish active workflow docs from archived execution history.

## Decision Log

- Decision: Use GitHub Issues as the single source of truth for task state.
  - Rationale: Better collaboration, audit trail, linking, and less branch-conflict risk than YAML state edits.
- Decision: Keep ExecPlans in `agents/plans/` and require each issue to link its ExecPlan path.
  - Rationale: Execution detail should remain versioned with code and reviewable in PRs.
- Decision: Accept temporary workflow breakage and avoid compatibility shims unless unblock is necessary.
  - Rationale: Faster migration with less dual-system complexity.

## Outcomes & Retrospective

Target outcome is a working Issue-native workflow where active work is discoverable via `gh issue` queries, each issue links one ExecPlan, and task progress no longer depends on `tasks.yaml` edits.

Current status: achieved for active role contracts, workflow prompt, issue template, and dispatcher tooling. Legacy references are retained only in archived historical plans/scratchpads.

## Context and Orientation

Migration impacts these files and surfaces:

- `agents/roles/architect.md`
- `agents/roles/executor.md`
- `agents/roles/reviewer.md`
- `agents/context/tasks.yaml` (retire from state-machine role)
- `agents/scripts/lint_tasks_state.py` (retire or repurpose)
- Any docs in `agents/context/` and `agents/instructions/` that refer to `tasks.yaml` status transitions

GitHub CLI (`gh`) is required for setup and validation.

## Plan of Work

1. Define the issue-based state model and label taxonomy.
2. Apply repository labels and issue template/checklist changes.
3. Rewrite role workflows to operate on GitHub Issues, not `tasks.yaml`.
4. Retire task-state linter/script dependencies and remove references.
5. Run a pilot on one task lifecycle and capture friction and fixes.

## Concrete Steps

1. Establish Issue status model and labels.
   - Define canonical labels: `task:ready`, `task:in_progress`, `task:blocked`, `task:ready_for_review`, `task:review_in_progress`, `task:done`.
   - Add support labels: `role:architect`, `role:executor`, `role:reviewer`, `kind:migration`.
   - Create/apply labels with `gh label create`/`gh label edit`.
2. Add or update Issue template(s).
   - Required fields: objective, scope, `execplan` path, validation commands, acceptance evidence, PR URL.
   - Include a checkbox list mirroring current completion gate requirements.
3. Update role contracts.
   - Architect: select/create GitHub Issue instead of task row.
   - Executor: transition labels in issue lifecycle and record PR URL in issue + ExecPlan.
   - Reviewer: use issue labels for review and done transitions after merge.
4. Retire `tasks.yaml` state machine.
   - Remove status-transition requirements from docs.
   - Either delete `agents/scripts/lint_tasks_state.py` or mark deprecated and remove from workflows.
   - Leave `tasks.yaml` as archived historical artifact or remove it in this migration PR.
5. Validate with one live lifecycle run.
   - Start from a new issue using the new template.
   - Execute one full Architect -> Executor -> Reviewer pass.
   - Confirm no step requires `tasks.yaml` edits.
6. Closeout documentation.
   - Add migration notes under `agents/context/` or `docs/` with rationale, outcomes, and known tradeoffs.

## Validation and Acceptance

Migration is accepted only when all are true:

- Role docs no longer require `agents/context/tasks.yaml` for state transitions.
- `tasks.yaml` is no longer referenced as authoritative state machine in active workflows.
- At least one issue completes full lifecycle using labels/checklists and linked ExecPlan.
- PR and merge evidence are discoverable from issue timeline and linked ExecPlan.
- `gh issue list` + label filters can reconstruct active queue without repo-local state files.

Suggested validation commands:

- `gh label list`
- `gh issue list --state open --label task:ready`
- `gh issue list --state open --label task:in_progress`
- `gh issue view <issue-number>`
- `git grep -n "tasks.yaml\|lint_tasks_state.py" agents/`

## Idempotence and Recovery

- Label/template creation is idempotent when using `gh label edit` for existing labels.
- If migration blocks active delivery, temporarily document manual fallback in role docs (issue comments + explicit status text) without reintroducing `tasks.yaml` authority.
- If partial changes land, prioritize fixing role-doc contradictions before further process updates.

## Artifacts and Notes

- Migration PR branch: TBD.
- Migration issue(s): `#6` (implementation issue), `#7` (lifecycle pilot validation).
- Any removed or deprecated files should be listed explicitly in the PR body.

## Interfaces and Dependencies

- GitHub repository issues and labels.
- GitHub CLI (`gh`) with authenticated access.
- Existing role docs and ExecPlan workflow prompt.

## Final Reflection Round

### Outcome
- Migrated active task tracking from repo-local YAML state to GitHub Issues + labels, with role docs, template, and tooling aligned.

### What Changed
- Added canonical label model and applied labels in GitHub: task-state labels, role labels, and `kind:migration`.
- Added GitHub issue template at `.github/ISSUE_TEMPLATE/task_execplan.yml` and config at `.github/ISSUE_TEMPLATE/config.yml`.
- Updated role contracts (`agents/roles/architect.md`, `agents/roles/executor.md`, `agents/roles/reviewer.md`) to use issue labels and `ExecPlan Path`.
- Updated workflow/context docs to remove active `tasks.yaml` authority and document issue-native process (`agents/context/github_issues_task_tracking.md`, `agents/context/contract.md`, `agents/context/codebase_map.md`, `agents/context/objectives.md`, `agents/context/project_status.md`, `agents/plans/README.md`, `agents/prompts/workflows/execplan.md`).
- Retired old state machine artifacts by deleting `agents/context/tasks.yaml` and `agents/scripts/lint_tasks_state.py`; preserved a historical snapshot at `agents/context/tasks_legacy_snapshot_2026-03-25.yaml`.
- Replaced `agents/scripts/task_dispatcher.py` scheduler logic to operate on GitHub issues (`--issues`, `--all-ready`) instead of `tasks.yaml`.

### Key Decisions and Trade-offs
- Chose a clean break (delete deprecated state files) instead of compatibility shims to avoid dual-source-of-truth drift.
- Kept historical plan/scratchpad references unchanged to preserve execution history fidelity, accepting residual grep hits in archival files.
- Implemented issue-based dispatcher rewiring in the same migration PR to avoid leaving contradictory "active" tooling.

### Lessons Learned
- Label transitions plus issue-template checklists can replace local linter-enforced state constraints for day-to-day coordination.
- A dedicated migration playbook doc (`agents/context/github_issues_task_tracking.md`) reduces ambiguity across roles faster than piecemeal role-only edits.
- Pilot lifecycle validation is easiest to prove with an explicit issue timeline showing label transitions and PR linkage.

### Memories to Promote
- Promote: always include `ExecPlan Path` as a required issue field so executor startup is deterministic.
- Promote: keep exactly one `task:*` and one `role:*` label on active issues to simplify queue reconstruction.

### Frictions and Complaints
- `git grep` still surfaces historical references from archived plans/scratchpads; this is expected noise during migration verification.

### Improvement Proposals
- Add a lightweight CI check that verifies open issues use exactly one `task:*` and one `role:*` label.
- Add a helper script for issue label transitions (start/ready-for-review/review/done) to reduce manual `gh issue edit` mistakes.

### Evidence
- `gh label list` shows canonical migration labels present (`task:*`, `role:*`, `kind:migration`).
- `gh issue list --state open --label task:in_progress` shows active issue `#6`.
- `gh issue view 6` confirms migration issue fields include `ExecPlan Path` and validation contract.
- `gh issue view 7` plus timeline comments show full pilot lifecycle transitions to `task:done` and closure.
- `git grep -n "tasks.yaml\|lint_tasks_state.py" agents/` now reports only migration docs, historical plans, and archival scratchpads (no active role/workflow dependency).
- `./venv/bin/python -m py_compile agents/scripts/task_dispatcher.py` passes.
- `./venv/bin/python agents/scripts/task_dispatcher.py --help` renders issue-based flags.

### Next Steps
- Open migration PR and link URL in issue `#6`.
- During review, verify no additional active docs/scripts reintroduce `tasks.yaml` authority.

---

Revision note (2026-03-25): Updated plan from proposed migration to executed state, including completed progress checkpoints, pilot issue evidence, retired files, and full final reflection details.
