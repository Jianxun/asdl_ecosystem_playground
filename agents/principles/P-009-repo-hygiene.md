# P-009 Repo Hygiene

## Intent

Keep the repository state clean and reviewable while iterating on experiments.

## Why

- Large uncommitted batches increase drift and make debugging harder.
- Small commits preserve intent and simplify rollback/review.
- A clean tree between tasks prevents cross-experiment contamination.

## Rules

- Commit often with small, coherent changes.
- Before starting a new experiment/task, ensure working tree is clean or intentionally scoped.
- Do not mix unrelated experiment changes in one commit.
- Keep generated run artifacts out of commits unless explicitly requested.
- Prefer small PRs mapped to one task/experiment milestone.
- Merge and prune promptly after review to avoid long-lived drift branches.

## Practical Workflow

1. Finish one logical change.
2. Run minimal verification for that change.
3. Commit with message explaining why.
4. Open/update a focused PR when scope is reviewable.
5. Merge promptly when approved; prune branch.
6. Confirm clean tree before switching context.

## PR Size Guidance

- Aim for one PR per coherent objective (for example one experiment, one tooling feature, one instruction update).
- If a branch grows across objectives, split into stacked PRs before adding more scope.
- If large scope is unavoidable, declare boundaries and known follow-up splits in the PR body.

## Exceptions

- If user requests a larger WIP batch, document scope boundaries clearly.
- If interrupted mid-task, record exact WIP state in scratchpad before switching.
