# P-001 Theory-Simulation Correlation

## Intent

Always correlate analytical expectations with simulation results, and validate workflows on deterministic circuits before scaling to complex designs.

## Why

- Prevents tool-flow mistakes from being misread as circuit behavior.
- Makes debugging explainable and faster.
- Creates objective pass/fail checkpoints for method validation.

## Rules

- For every key metric, state the theoretical expectation and simulation value side by side.
- Prefer deterministic reference fixtures (idealized or reduced-order models) before applying methods to real circuits.
- Introduce complexity incrementally and keep each step explainable.
- When mismatch appears, isolate whether root cause is:
  - equation/sign convention,
  - probing/observability,
  - model/circuit non-ideality,
  - simulator/setup artifact.

## Required Reporting Pattern

- Include formulas used for expected values.
- Include measured values and percent error.
- Include a brief interpretation of whether mismatch is acceptable and why.
