# Experiment Report: T-010 `inv_dc` on Xyce

## Metadata
- id: T-010
- date: 2026-03-01
- owner: Executor
- backend: sim.xyce
- simulator: Xyce DEVELOPMENT-202602210047 (Release-7.10.0)

## Goal
- Validate the minimal end-to-end ASDL flow for a GF180 CMOS inverter DC sweep: author -> compile -> simulate -> normalize.

## Inputs
- ASDL files:
  - `libs/exp_010_hello_xyce/inv.asdl`
  - `libs/exp_010_hello_xyce/tb.asdl`
- Config files:
  - `.asdlrc`
  - `config/backends.yaml`
- Exact commands run from repo root:
  - `./venv/bin/asdlc netlist libs/exp_010_hello_xyce/tb.asdl --backend sim.xyce`
  - `mkdir -p runs/exp_010_hello_xyce/20260301T070037Z`
  - `./venv/bin/asdlc netlist libs/exp_010_hello_xyce/tb.asdl --backend sim.xyce -o runs/exp_010_hello_xyce/20260301T070037Z/tb.spice`
  - `xyce runs/exp_010_hello_xyce/20260301T070037Z/tb.spice`
  - `./venv/bin/python analysis/tools/xyce/raw_to_h5.py runs/exp_010_hello_xyce/20260301T070037Z/tb.spice.raw`

## Outputs
- Emitted netlist path:
  - `runs/exp_010_hello_xyce/20260301T070037Z/tb.spice`
- Simulator output path:
  - `runs/exp_010_hello_xyce/20260301T070037Z/tb.spice.raw`
- Parsed metrics path:
  - `runs/exp_010_hello_xyce/20260301T070037Z/tb.spice.raw.h5`

## Result
- pass/fail: pass
- key measurements:
  - Xyce DC sweep completed with 331 successful steps and 0 failed steps.
  - Device count: 1 inverter DUT (2 MOSFETs) + 3 voltage sources.
- anomalies:
  - Xyce emits repeated GF180 model warnings (`MODEL_BINNING` duplicate parser parameter and low `pbswgd` clamp) from PDK model cards.

## Tooling Notes
- Diagnostics quality observations:
  - ASDL compiler error messages were actionable for unresolved instance references.
  - Xyce warnings are verbose and repeated; still non-fatal for this run.
- Workflow friction points:
  - First attempt used `sim.save_dc`, which is not defined in `simulation.xyce.asdl`; correct primitive is `sim.save sim_type=DC`.
  - First normalization attempt failed because `h5py` was missing in the local virtual environment.
- Suggested fixes:
  - Add a short `sim.save` usage example with `sim_type=DC` to `agents/instructions/snippets.md`.
  - Add `h5py` to project bootstrap dependencies or quickstart checks for normalization prerequisites.
