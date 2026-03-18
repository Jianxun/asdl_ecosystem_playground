# Skill: PR Cycle Hygiene

## Purpose

Keep branch, commit, and PR flow tight so work stays reviewable and does not drift across unrelated tasks.

## Uses Principles

- `P-002` incremental modular construction
- `P-007` experiment analysis recipe
- `P-009` repo hygiene

## When to Use

- Any multi-file implementation task
- Experiment work that can exceed one session
- Tooling + experiment updates in the same branch

## Workflow

1. **Define PR scope first**
   - one objective per PR (feature, experiment milestone, or guidance update)
2. **Implement in small increments**
   - each increment ends with minimal verification and a coherent commit
3. **Open/update PR early**
   - keep title/body aligned to current scope
4. **Control drift continuously**
   - if unrelated changes appear, split to a new branch/PR
5. **Merge and prune quickly**
   - once approved and green, merge and delete branch
6. **Reset for next objective**
   - start next task from clean `main`/fresh branch

## Commit Grouping Heuristic

- commit 1: structure/instructions
- commit 2: core code or testbenches
- commit 3: analysis scripts/reports
- commit 4: cleanup/hygiene (gitignore, artifact removals)

Adjust grouping to fit scope, but avoid mixing unrelated objectives.

## PR Checklist

- scope is single objective
- generated artifacts excluded unless requested
- formulas and measurement conventions documented
- rerun commands and expected checkpoints included
- branch clean after merge
