# T-101 — Build ngspice fixture netlists and runner

## Objective
Create 3 deterministic fixture netlists and a runner to produce RAW outputs.

## Scope
- Netlists: `tran_square`, `tran_multitone`, `ac_onepole`.
- Runner: `scripts/run_fixtures.py`.
- Output layout: `outputs/raw/<case>/{netlist.spice,*.raw,sim.log}`.

## DoD
- One command runs all fixtures.
- 3 RAW files generated.
- Logs captured per case.
