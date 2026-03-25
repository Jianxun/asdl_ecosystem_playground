# Playbook

Single source of truth for how agents should execute ASDL Playground labs.

## Scope

- This repo is an ergonomics playground, not a conformance suite.
- Each lab should answer one practical authoring/tooling question.

## Canonical conventions (normative)

- Run commands from repo root.
- Default backend: `sim.ngspice` unless explicitly comparing backends.
- Keep source artifacts in `labs/<lab-id>/`.
- Keep generated artifacts in `labs/<lab-id>/artifacts/`.
- One baseline lab run is sufficient for now; overwriting prior local artifacts is acceptable.
- Use explicit input/output paths for compile, simulation, and normalization commands.

## Required outputs per lab (normative)

- One source library under `labs/<lab-id>/`.
- One local artifact set under `labs/<lab-id>/artifacts/`.
- One lab write-up under `labs/<lab-id>/lab.md`.
- One or more instruction updates in `agents/instructions/` when new guidance emerges.

## Canonical toolchain

- Compiler: `asdlc`
- Simulator: `ngspice`
- Normalization:
  - `analysis/tools/ngspice/normalize_raw.py`

## Minimal run loop

```bash
# compile sanity check
asdlc netlist labs/<lab-id>/asdl/tb.asdl --backend sim.ngspice

# compile to local lab artifacts
asdlc netlist labs/<lab-id>/asdl/tb.asdl --backend sim.ngspice -o labs/<lab-id>/artifacts/tb.spice

# simulate
ngspice -b -o labs/<lab-id>/artifacts/ngspice.log labs/<lab-id>/artifacts/tb.spice

# normalize
./venv/bin/python analysis/tools/ngspice/normalize_raw.py --input labs/<lab-id>/artifacts/tb.raw --output labs/<lab-id>/artifacts/tb.hdf5

# plot from normalized data
./venv/bin/python labs/<lab-id>/scripts/plot_from_hdf5.py --input labs/<lab-id>/artifacts/tb.hdf5 --out labs/<lab-id>/figures
```

## Warning handling

- Treat repeated simulator/model-card warnings as warnings unless simulator exit status is non-zero.

## Import conventions

- Use one import style per source to reduce ambiguity.
- For PDK and shared libs, use root-resolved names (for example `gf180mcu.asdl`, `analoglib.asdl`, `simulation.ngspice.asdl`).
- For local dependencies, prefer `./...` imports from the same lab folder.
- For portability, prefer copying dependent DUT files into the same `labs/<lab-id>/` folder instead of reaching across other lab trees.

## Reporting contract

Always capture:

- exact commands run
- exact artifact paths produced
- first-run friction (first failing command, exact error text, fix)
- suggested updates to instructions/snippets/tooling
