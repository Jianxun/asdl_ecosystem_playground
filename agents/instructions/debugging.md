# Debugging Guide

Fast triage path for agent-run ASDL experiments.

## Step 1: classify the failure

- **Compile-time**: `asdlc` fails.
- **Runtime**: Xyce fails to run or converges poorly.
- **Post-processing**: normalization scripts fail or outputs are malformed.

## Step 2: common checks

1. Confirm `.asdlrc` points to valid paths (`config/`, `pdks/`, `libs_common/`, `libs/`).
2. Confirm experiment source is under `libs/`, not `examples/`.
3. Confirm outputs are written to `runs/`.
4. Confirm backend is `sim.xyce` unless experiment explicitly compares backends.

## Compile-time failure checklist

- Missing import:
  - Verify import path and module symbol spelling.
- Unknown device/module:
  - Verify library roots and module name.
- Unresolved simulation primitive (for example `sim.save_dc`):
  - Check `libs_common/simulation.xyce.asdl` for supported names.
  - Use `sim.save sim_type=<analysis>` instead of `sim.save_dc`.
- Net/port mismatch:
  - Re-check port names and net fanout declarations.

## Runtime failure checklist (Xyce)

- Missing model include:
  - Verify PDK include paths and `.lib` references in emitted deck.
- Convergence issues:
  - Reduce stimulus aggressiveness, check initial conditions, simplify bench.
- Empty/unexpected outputs:
  - Verify `.PRINT`/save directives and analysis statements.
- Analysis/print mismatch error:
  - If Xyce reports `Analysis type <A> and print type <B> are inconsistent`, split mixed analyses into separate decks (for example one AC deck and one TRAN deck) so each `.PRINT` matches the active analysis.

## Post-processing failure checklist

- RAW missing or corrupted:
  - Verify simulation completed and produced expected files.
- `raw_to_h5.py` errors:
  - Check RAW flags/format and script input path.
  - If error mentions missing `h5py`, install in project venv:
    - `./venv/bin/pip install h5py numpy`
- OP pivot errors:
  - Confirm input is OP-like table with device parameter headers.

## Reporting rule

When blocked, always record:

- exact failing command
- exact error text
- suspected cause
- next attempted fix
