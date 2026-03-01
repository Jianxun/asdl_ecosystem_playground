# Quickstart

Use this to run one complete loop with minimal decisions.

## 1) Verify environment

From repo root:

```bash
./venv/bin/python --version
asdlc --help
xyce -v
./venv/bin/python -c "import numpy, h5py; print('ok')"
```

If `xyce` is missing, stop and note the missing dependency in the experiment report.

If the Python dependency check fails, install in the local venv:

```bash
./venv/bin/pip install numpy h5py
```

## 2) Pick or create an experiment library

- Canonical location: `libs/<experiment_name>/`
- Keep only source assets in `libs/` (`.asdl`, bench configs, small notes).
- Put generated outputs in `runs/<experiment_name>/<run_id>/`.

## 3) Compile

```bash
asdlc netlist libs/<experiment_name>/tb.asdl --backend sim.xyce
```

## 4) Run simulation (Xyce default)

```bash
xyce runs/<experiment_name>/<run_id>/tb.spice
```

## 5) Normalize outputs

```bash
./venv/bin/python analysis/tools/xyce/raw_to_h5.py runs/<experiment_name>/<run_id>/tb.spice.raw
./venv/bin/python analysis/tools/xyce/format_xyce_op_csv.py runs/<experiment_name>/<run_id>/tb.spice.FD.prn
```

## 6) Record findings

Create/update a report in `docs/` using `experiment_template.md` and include:

- exact commands
- runtime artifacts
- friction points (what was confusing or fragile)
- recommended workflow/tooling improvements
