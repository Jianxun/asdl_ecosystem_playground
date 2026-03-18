# P-002 Incremental Modular Construction

## Intent

Build analog circuits and testbenches incrementally: validate smaller blocks first, then compose into larger systems.

## Why

- One-shot assembly of complex circuits is brittle and hard to debug.
- Early block-level validation reduces integration uncertainty.
- ASDL hierarchy is lightweight; use that to refactor modules aggressively.

## Rules

- Start with the smallest meaningful subcircuit and verify standalone behavior.
- Compose verified subcircuits into higher-level modules step by step.
- At each composition step, run targeted checks before adding more complexity.
- Refactor hierarchy when needed; do not keep monolithic benches if modularization improves clarity.

## ASDL-Specific Guidance

- Prefer small reusable modules over large flat netlists.
- Use local experiment imports (`./...`) for portable composition.
- Keep module interfaces explicit (`$ports`) so sub-block behavior can be isolated easily.

## Exit Criteria per Step

- Expected local behavior is verified.
- Required observables are present for next integration step.
- New complexity added is justified and documented.
