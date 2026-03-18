# Playbook

Single source of truth for how agents should execute ASDL Playground experiments.

## Scope

- This repo is an ergonomics playground, not a conformance suite.
- Each experiment should answer one practical authoring/tooling question.

## Canonical conventions (normative)

- Run commands from repo root.
- Default backend: `sim.xyce` unless explicitly comparing backends.
- Keep source artifacts in `libs/<experiment_name>/`.
- Keep generated artifacts in `runs/<experiment_name>/<run_id>/`.
- Use explicit input/output paths for compile, simulation, and normalization commands.

## Required outputs per experiment (normative)

- One source library under `libs/<experiment_name>/`.
- One reproducible run folder under `runs/<experiment_name>/<run_id>/`.
- One report in `docs/` using `experiment_template.md`.
- One or more instruction updates in `agents/instructions/` when new guidance emerges.

## Canonical toolchain

- Compiler: `asdlc`
- Simulator: `xyce`
- Normalization:
  - `analysis/tools/xyce/raw_to_h5.py`
  - `analysis/tools/xyce/format_xyce_op_csv.py`

## Minimal run loop

```bash
# compile sanity check
asdlc netlist libs/<experiment_name>/tb.asdl --backend sim.xyce

# compile to run folder
asdlc netlist libs/<experiment_name>/tb.asdl --backend sim.xyce -o runs/<experiment_name>/<run_id>/tb.spice

# simulate
xyce runs/<experiment_name>/<run_id>/tb.spice

# normalize
./venv/bin/python analysis/tools/xyce/raw_to_h5.py runs/<experiment_name>/<run_id>/tb.spice.raw
./venv/bin/python analysis/tools/xyce/format_xyce_op_csv.py runs/<experiment_name>/<run_id>/tb.spice.FD.prn
```

## Warning handling

- Treat repeated GF180 model-card warnings in Xyce (for example `MODEL_BINNING` or `pbswgd` clamp notices) as warnings unless simulator exit status is non-zero.

## Import conventions

- Use one import style per source to reduce ambiguity.
- For PDK and shared libs, use root-resolved names (for example `gf180mcu.asdl`, `analoglib.asdl`, `simulation.xyce.asdl`).
- For local dependencies, prefer `./...` imports from the same experiment folder.
- For portability, prefer copying dependent DUT files into the same `libs/<experiment>/` folder instead of reaching across other experiment trees.

## Reporting contract

Always capture:

- exact commands run
- exact artifact paths produced
- first-run friction (first failing command, exact error text, fix)
- suggested updates to instructions/snippets/tooling
