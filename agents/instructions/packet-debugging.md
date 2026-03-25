# Packet: Debugging

Fast triage path for ASDL lab failures.

**Inject when:** A compile, simulation, or post-processing step fails.

## Step 1: Classify the failure

- **Compile-time**: `asdlc` exits non-zero.
- **Simulation-time**: `ngspice` exits non-zero or produces no output.
- **Post-processing**: normalization or plot scripts fail.

## Step 2: Common checks

1. Confirm `.asdlrc` points to valid paths (`config/`, `pdks/`, `libs_common/`).
2. Confirm source is under `labs/`, not `examples/`.
3. Confirm artifacts are written to `labs/builds/<lab-id>/artifacts/`.
4. Confirm backend is `sim.ngspice` unless explicitly comparing backends.

## Compile-time failure checklist

- **Missing import**: verify import path and module symbol spelling.
- **Unknown device/module**: verify library roots in `.asdlrc` and module name.
- **Unresolved simulation primitive** (e.g., `sim.save_dc`):
  - Check `libs_common/simulation.ngspice.asdl` for supported names.
  - Use `sim.save sim_type=<analysis>` (see `les-200a5ad7`).
- **Net/port mismatch**: re-check port names and net fanout declarations.

## Simulation-time failure checklist (ngspice)

- **Missing model include**: verify PDK include paths in `.asdlrc` and emitted netlist.
- **Convergence issues**: reduce stimulus aggressiveness, check initial conditions, simplify bench.
- **Empty/unexpected outputs**: verify save directives and analysis statements in emitted netlist.
- **Analysis/print mismatch**: ensure `.PRINT` type matches active analysis type.

## Post-processing failure checklist

- **RAW missing or corrupted**: verify simulation completed and produced expected files.
- **`normalize_raw.py` errors**:
  - Check RAW format and `--input` path.
  - If `h5py` missing: `./venv/bin/pip install h5py numpy`
- **Plot script errors**: confirm HDF5 file exists and signal names match expectations.

## Reporting rule

When blocked, always record:
- exact failing command
- exact error text
- suspected cause
- next attempted fix
