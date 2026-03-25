# Quickstart

Use this to run one complete loop with minimal decisions.

Primary policy lives in `playbook.md`; this file is the fastest checklist.

## 1) Verify environment

From repo root:

```bash
./venv/bin/python --version
asdlc --help
ngspice -v
./venv/bin/python -c "import numpy, h5py; print('ok')"
```

If `ngspice` is missing, stop and note the missing dependency in the lab report.

If the Python dependency check fails, install in the local venv:

```bash
./venv/bin/pip install numpy h5py
```

## 2) Pick or create a lab

- Canonical location: `labs/<lab-id>/`
- Keep source assets under `labs/<lab-id>/asdl/` and scripts under `labs/<lab-id>/scripts/`.
- Put generated outputs under `labs/<lab-id>/artifacts/` (single overwriteable baseline is acceptable).

## 3) Compile

```bash
asdlc netlist labs/<lab-id>/asdl/tb.asdl --backend sim.ngspice
```

## 4) Run simulation (ngspice default)

```bash
ngspice -b -o labs/<lab-id>/artifacts/ngspice.log labs/<lab-id>/artifacts/tb.spice
```

## 5) Normalize outputs

```bash
./venv/bin/python analysis/tools/ngspice/normalize_raw.py --input labs/<lab-id>/artifacts/tb.raw --output labs/<lab-id>/artifacts/tb.hdf5
./venv/bin/python labs/<lab-id>/scripts/plot_from_hdf5.py --input labs/<lab-id>/artifacts/tb.hdf5 --out labs/<lab-id>/figures
```

## 6) Record findings

Create/update a report in `docs/` using `experiment_template.md` and include:

- exact commands
- runtime artifacts
- friction points (what was confusing or fragile)
- recommended workflow/tooling improvements

If guidance changes, update one or more files under `agents/instructions/`.
