# ExecPlan Workflow Prompt

This document defines the standard for writing and maintaining an execution plan (ExecPlan).

An ExecPlan must be self-contained: a new contributor should be able to complete the work using only the working tree and the ExecPlan file.

## Core principles

Every ExecPlan must satisfy these requirements:

- It is self-contained and novice-readable.
- It is a living document that is updated as work progresses.
- It describes user-visible outcomes, not just code edits.
- It includes concrete validation commands and expected observations.
- It records key decisions and their rationale.
- It is linked from exactly one GitHub Issue via `ExecPlan Path`.

Use plain language. Define repository-specific terms the first time they appear.

## Required sections

Use this section order in each ExecPlan:

1. `# <Short action-oriented title>`
2. `## Purpose / Big Picture`
3. `## Progress`
4. `## Surprises & Discoveries`
5. `## Decision Log`
6. `## Outcomes & Retrospective`
7. `## Context and Orientation`
8. `## Plan of Work`
9. `## Concrete Steps`
10. `## Validation and Acceptance`
11. `## Idempotence and Recovery`
12. `## Artifacts and Notes`
13. `## Interfaces and Dependencies`
14. `## Final Reflection Round`

`Progress` must use checkboxes and timestamps.

## Formatting

- Write prose-first. Use lists only where they improve clarity.
- Keep commands explicit, including working directory assumptions.
- When showing snippets, keep them concise and focused on proof.
- If the ExecPlan is the full content of a `.md` file, do not wrap it in code fences.

## Validation standard

Validation is mandatory. Include exact commands and what success/failure looks like.

Acceptance must be observable behavior, not internal implementation claims.

For execution tasks that include git closeout expectations, acceptance is incomplete until all of the following are true and recorded in the ExecPlan: feature branch exists, validation evidence is captured, branch is pushed, PR to `main` is open, and PR URL is documented.

For issue-driven tasks, acceptance is also incomplete until the linked issue timeline shows the expected task-state label transitions and the PR URL is present in the issue body or comments.

## Final Reflection Round

The reflection is required before handoff. It should be completed at the end of execution, after implementation and validation are done.

The reflection section must include the following subsections:

- `### Outcome` (mandatory)
- `### What Changed` (mandatory)
- `### Key Decisions and Trade-offs` (mandatory)
- `### Lessons Learned` (mandatory)
- `### Memories to Promote` (conditionally required; use `- Not applicable.` when none)
- `### Frictions and Complaints` (conditionally required; use `- Not applicable.` when none)
- `### Improvement Proposals` (mandatory)
- `### Evidence` (mandatory)
- `### Next Steps` (conditionally required; use `- Not applicable.` when none)

Reflection quality bar:

- Claims are evidence-backed (commands, artifacts, diffs, tests, PR context).
- Facts are separated from conclusions.
- Improvement proposals are actionable and scoped.
- Placeholders like `TBD` are not allowed at handoff.

Recommended stub to pre-populate in every new ExecPlan:

    ## Final Reflection Round

    ### Outcome
    - TBD

    ### What Changed
    - TBD

    ### Key Decisions and Trade-offs
    - TBD

    ### Lessons Learned
    - TBD

    ### Memories to Promote
    - TBD

    ### Frictions and Complaints
    - TBD

    ### Improvement Proposals
    - TBD

    ### Evidence
    - TBD

    ### Next Steps
    - TBD

## Revision note requirement

When you revise an ExecPlan, update all affected sections for consistency and append a short revision note at the bottom explaining what changed and why.
