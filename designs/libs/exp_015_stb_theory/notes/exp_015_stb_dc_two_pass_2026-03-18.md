# Experiment Report: EXP-015 DC Two-Pass Validation (Generic `Gm-Go-Gi`)

## Metadata
- id: exp_015_stb_dc_two_pass
- date: 2026-03-18
- owner: OpenCode agent session with user guidance
- backend: sim.xyce
- simulator: Xyce DEVELOPMENT-202602210047

## Goal
- Validate the canonical two-pass Middlebrook/Tian conventions on a pure-resistive, ground-referenced fixture before moving to frequency-dependent impedances.

## Setup
- Theory reference:
  - `docs/theories/loop_gain_analysis_middlebrook_tian.md`
- DUT:
  - `libs/exp_015_stb_theory/ideal_gm_go_gi_cell.asdl`
- Series pass (DC proxy for AC1):
  - `libs/exp_015_stb_theory/tb_dc_middlebrook_series.asdl`
- Shunt pass (DC proxy for AC2):
  - `libs/exp_015_stb_theory/tb_dc_middlebrook_shunt.asdl`
- Parameters:
  - `Gm=1e-3 S`, `Go=2e-4 S` (`Ro=5k`), `Gi=1e-4 S` (`Ri=10k`)

## Commands
```bash
RUN_ID=20260318T174956Z
RUN_DIR=runs/exp_015_stb_theory/${RUN_ID}

asdlc netlist libs/exp_015_stb_theory/tb_dc_middlebrook_series.asdl --backend sim.xyce -o ${RUN_DIR}/tb_dc_middlebrook_series.spice
asdlc netlist libs/exp_015_stb_theory/tb_dc_middlebrook_shunt.asdl --backend sim.xyce -o ${RUN_DIR}/tb_dc_middlebrook_shunt.spice

xyce ${RUN_DIR}/tb_dc_middlebrook_series.spice
xyce ${RUN_DIR}/tb_dc_middlebrook_shunt.spice

./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_dc_middlebrook_series.spice.raw
./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_dc_middlebrook_shunt.spice.raw

./venv/bin/python analysis/tools/xyce/analyze_middlebrook_dc_two_pass.py \
  ${RUN_DIR} --gm 1e-3 --go 2e-4 --gi 1e-4
```

## Artifacts
- run directory:
  - `runs/exp_015_stb_theory/20260318T174956Z`
- normalized outputs:
  - `runs/exp_015_stb_theory/20260318T174956Z/tb_dc_middlebrook_series.spice.raw.h5`
  - `runs/exp_015_stb_theory/20260318T174956Z/tb_dc_middlebrook_shunt.spice.raw.h5`
- analysis metrics:
  - `runs/exp_015_stb_theory/20260318T174956Z/metrics_middlebrook_dc_two_pass.json`

## Results
- Series-pass voltage ratio:
  - measured `Tv = -Vr/Vf = 5.5`
  - theory `Tv = (Gm+Gi)/Go = 5.5`
- Shunt-pass current ratio:
  - measured `Ti = Iout/Iin = 12.0`
  - theory `Ti = (Go+Gm)/Gi = 12.0`
- Tian reconstructed loop gain:
  - measured `T = 3.3333333333`
  - theory `T = Gm/(Go+Gi) = 3.3333333333`

## Takeaway
- The exact canonical conventions are numerically consistent on the simplest resistive baseline.
- This clears the path to extend the same bench topology and analyzer conventions to RC frequency-dependent runs.
