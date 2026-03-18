# P-008 Close the Loop on Guidance

## Intent

When a lesson is stable and reusable, encode it back into repository guidance promptly.

## Why

- Prevents repeating the same friction in later sessions.
- Turns one-off troubleshooting into cumulative process improvement.

## Rules

- Promote stable lessons to `agents/principles/` with a new ID.
- Update `agents/principles/README.md` index in same change.
- Reference related principle IDs in experiment summaries when relevant.
- Prefer additive updates over broad rewrites unless structural consolidation is needed.
