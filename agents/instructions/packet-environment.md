# Packet: Environment Setup

Fast environment verification checklist for ASDL Playground.

**Inject when:** Starting a new session or after environment changes.

## Verify environment

From repo root:

```bash
./venv/bin/python --version
asdlc --help
ngspice -v
./venv/bin/python -c "import numpy, h5py; print('ok')"
```

If `ngspice` is missing: stop and note the missing dependency.

If the Python dependency check fails:
```bash
./venv/bin/pip install numpy h5py
```

## Configuration pointers

- Repo config: `.asdlrc` (sets backend config, lib roots, env vars)
- Backend templates: `config/backends.yaml`
- Shared libraries: `libs_common/`
- PDK assets: `pdks/`

## Key environment variables (set by .asdlrc)

- `PDK` — active PDK name (e.g., `gf180mcu`)
- `PDK_PATH` — path to PDK root
- `ASDL_DESIGN_LIBS_PATH` — resolved design library search path

## Lab directory structure

```
labs/
  specs/<lab-id>.yaml          ← stable spec (never regenerated)
  plans/<lab-id>.md            ← architect-generated plan (regenerable)
  builds/<lab-id>/
    asdl/                      ← source files
    scripts/                   ← analysis and plot scripts
    artifacts/                 ← generated simulation outputs (git-ignored by extension)
    figures/                   ← generated plots
    lab.md                     ← lab write-up
```
