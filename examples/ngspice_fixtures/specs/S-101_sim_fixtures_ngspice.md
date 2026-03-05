# S-101 — Minimal Simulation Fixtures (ngspice RAW producers)

## Objective
Create deterministic SPICE fixtures that generate RAW files for normalization and analyzer validation.

## Scope
- Add fixture netlists:
  - `netlists/tran_square.spice`
  - `netlists/tran_multitone.spice`
  - `netlists/ac_onepole.spice`
- Add runner script to execute all fixtures with ngspice and emit outputs into `outputs/raw/<case>/`.
- Store simulator logs per case.

## Out of Scope
- Xyce execution in this phase.
- Process-corner model libraries.

## Definition of Done (DoD)
- One command creates 3 RAW files and logs.
- Output paths are deterministic and documented.
- Fixtures are simple, readable, and reproducible.
