# T-010 — Bootstrap hello-flow with GF180 inverter on Xyce

## Task summary (DoD + verify)
- DoD: Build a minimal GF180 CMOS inverter experiment (`inv_dc`) in `libs/exp_010_hello_xyce/` with one DUT and one DC testbench. Run the full loop (compile, Xyce simulate, RAW to HDF5 normalization). Capture exact commands and first-run friction in a report.
- Verify:
  - `./venv/bin/asdlc netlist libs/exp_010_hello_xyce/tb.asdl --backend sim.xyce`
  - `./venv/bin/python analysis/tools/xyce/raw_to_h5.py runs/exp_010_hello_xyce/<run_id>/tb.spice.raw`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`

## Plan
- Create experiment library under `libs/exp_010_hello_xyce/` with inverter DUT + DC testbench.
- Compile to Xyce netlist and run simulation to produce RAW outputs in `runs/`.
- Normalize RAW to HDF5 and document exact commands plus first-run friction in `docs/`.
- Verify required commands and prepare closeout artifacts.

## Milestone notes
- Intake complete; task set to `in_progress`.
- Implemented minimal inverter DUT + DC testbench in `libs/exp_010_hello_xyce/`.
- First compile failed on unresolved `sim.save_dc`; fixed by switching to `sim.save sim_type=DC`.
- Xyce run completed on `runs/exp_010_hello_xyce/20260301T070037Z/tb.spice`.
- First normalization failed due to missing `h5py`; installed dependency in local venv and reran successfully.
- Updated hydration docs in `agents/instructions/` with dependency preflight, canonical save syntax, warning interpretation, and first-run friction capture fields.
- Appended multiple `[T-010][executor]` lessons to `agents/context/lessons.md`.

## Patch summary
- Added experiment sources:
  - `libs/exp_010_hello_xyce/inv.asdl`
  - `libs/exp_010_hello_xyce/tb.asdl`
- Added experiment report:
  - `docs/exp_010_hello_xyce_2026-03-01.md`
- Updated hydration pack guidance:
  - `agents/instructions/quickstart.md`
  - `agents/instructions/snippets.md`
  - `agents/instructions/debugging.md`
  - `agents/instructions/tooling.md`
  - `agents/instructions/workflow.md`
  - `agents/instructions/experiment_template.md`
- Added lessons:
  - `agents/context/lessons.md`
- Updated task scratchpad progress and verification notes.

## PR URL
- Pending.

## Verification
- `./venv/bin/asdlc netlist libs/exp_010_hello_xyce/tb.asdl --backend sim.xyce` -> pass
- `xyce runs/exp_010_hello_xyce/20260301T070037Z/tb.spice` -> pass (non-fatal GF180 model warnings)
- `./venv/bin/python analysis/tools/xyce/raw_to_h5.py runs/exp_010_hello_xyce/20260301T070037Z/tb.spice.raw` -> pass after installing `h5py`

## Status request (Done / Blocked / In Progress)
- In Progress.

## Blockers / Questions
- None.

## Next steps
- Decide whether to continue directly to closeout (PR + status `ready_for_review`) in this session or do additional cleanup in follow-up chunk.
