# P-006 Observability-Driven Probing

## Intent

Design testbench probes around required observables for the final equation, not only around topology.

## Why

- A mathematically correct method fails if required currents/voltages are not saved.
- Degenerate measurements are common when sense paths are missing.

## Rules

- List required observables before building the bench.
- Ensure each run emits all required signals in raw/h5 outputs.
- Add explicit sense elements when simulator output does not expose branch currents directly.
- Validate non-degeneracy with quick checks before deep analysis.

## Quick Non-Degeneracy Checks

- Verify measured quantities are not identically zero or identical by construction.
- Verify run-to-run observables differ in expected ways when injection mode changes.
