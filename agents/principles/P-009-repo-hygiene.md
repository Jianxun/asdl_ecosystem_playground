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

## Practical Workflow

1. Finish one logical change.
2. Run minimal verification for that change.
3. Commit with message explaining why.
4. Confirm clean tree before switching context.

## Exceptions

- If user requests a larger WIP batch, document scope boundaries clearly.
- If interrupted mid-task, record exact WIP state in scratchpad before switching.
