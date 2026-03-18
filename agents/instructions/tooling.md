# Tooling

Reference for tools used by the playground. Normative execution policy is in `playbook.md`.

## Compiler and simulator

- Compiler: `asdlc`
- Default backend for experiments: `sim.xyce`
- Simulator workhorse: `xyce`

## Post-processing (canonical)

- `analysis/tools/xyce/raw_to_h5.py`
  - Converts Xyce RAW outputs to hierarchical HDF5.
  - This is the primary normalization path for waveform-like outputs.
- `analysis/tools/xyce/format_xyce_op_csv.py`
  - Pivots OP-style tables to rows=device, columns=parameter.
  - Use for quick operating-point inspection.

Legacy scripts in library folders are intentionally removed.

## Configuration

- Repo config: `.asdlrc`
- Backend templates: `config/backends.yaml`
- Shared libraries: `libs_common/`
- PDK assets: `pdks/`

## Expected command style

- Run commands from repo root.
- Prefer explicit input/output paths.
- Persist all generated artifacts under `runs/`.
- Treat repeated GF180 model-card warnings in Xyce (for example `MODEL_BINNING` and `pbswgd` clamp notices) as warnings unless the simulator exits non-zero.

Example:

```bash
asdlc netlist libs/<experiment>/tb.asdl --backend sim.xyce
xyce runs/<experiment>/<run_id>/tb.spice
./venv/bin/python analysis/tools/xyce/raw_to_h5.py runs/<experiment>/<run_id>/tb.spice.raw
```
