# Packet: Lab Workflow

Normative execution policy for ASDL Playground labs.

**Inject when:** Starting any lab authoring or execution task.

## Scope

- This repo is a teaching-first lab system, not a conformance suite.
- Each lab answers one circuit concept with theory + simulation evidence.

## Canonical conventions

- Run all commands from repo root.
- Default backend: `sim.ngspice` unless explicitly comparing backends.
- Source assets live in `labs/builds/<lab-id>/asdl/` and `labs/builds/<lab-id>/scripts/`.
- Generated artifacts live in `labs/builds/<lab-id>/artifacts/` — single overwriteable baseline is acceptable.
- Use explicit input/output paths for all compile, simulation, and normalization commands.

## Execution loop

1. **Define objective** — one circuit concept, one key property or tradeoff.
2. **Author ASDL** — add only what is needed to demonstrate the concept.
3. **Compile sanity check** — catch errors before artifact emission:
   ```bash
   asdlc netlist labs/builds/<lab-id>/asdl/tb.asdl --backend sim.ngspice
   ```
4. **Compile to artifacts**:
   ```bash
   asdlc netlist labs/builds/<lab-id>/asdl/tb.asdl --backend sim.ngspice -o labs/builds/<lab-id>/artifacts/tb.spice
   ```
5. **Simulate**:
   ```bash
   ngspice -b -o labs/builds/<lab-id>/artifacts/ngspice.log labs/builds/<lab-id>/artifacts/tb.spice
   ```
6. **Normalize** (RAW → HDF5):
   ```bash
   ./venv/bin/python analysis/tools/ngspice/normalize_raw.py \
     --input labs/builds/<lab-id>/artifacts/tb.raw \
     --output labs/builds/<lab-id>/artifacts/tb.hdf5
   ```
7. **Plot from HDF5**:
   ```bash
   ./venv/bin/python labs/builds/<lab-id>/scripts/plot_from_hdf5.py \
     --input labs/builds/<lab-id>/artifacts/tb.hdf5 \
     --out labs/builds/<lab-id>/figures
   ```
8. **Write lab.md** — theory first, then simulation results, then comparison.

## Required outputs per lab

| Stage | Location | Stable? |
|---|---|---|
| Spec | `labs/specs/<lab-id>.yaml` | Yes — authored once, never regenerated |
| Plan | `labs/plans/<lab-id>.md` | No — regenerable from spec |
| ASDL source | `labs/builds/<lab-id>/asdl/` | No — regenerable from plan |
| Simulation artifacts | `labs/builds/<lab-id>/artifacts/` | No — regenerable |
| Figures | `labs/builds/<lab-id>/figures/` | No — script-generated |
| Lab write-up | `labs/builds/<lab-id>/lab.md` | No — regenerable |

## Import conventions

- PDK and shared libs: use root-resolved names (`gf180mcu.asdl`, `analoglib.asdl`, `simulation.ngspice.asdl`).
- Local dependencies: use `./...` imports from the same lab folder.
- For portability, copy dependent DUT files into the same `labs/builds/<lab-id>/` folder.

## Scope control

- Prefer short, focused labs over broad sweeps.
- Avoid framework abstractions before two or more labs need them.
- When uncertain, choose explicit commands over hidden automation.

## Reporting contract

Always capture:
- exact commands run and artifact paths produced
- first-run friction (first failing command, exact error text, fix applied)
- theory expectation and simulation result side by side with percent error
