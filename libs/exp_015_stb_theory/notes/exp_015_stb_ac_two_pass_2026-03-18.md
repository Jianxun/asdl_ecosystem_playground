# Experiment Report: EXP-015 AC Two-Pass Validation (Generic `Gm-Go-Gi` RC)

## Metadata
- id: exp_015_stb_ac_two_pass
- date: 2026-03-18
- owner: OpenCode agent session with user guidance
- backend: sim.xyce
- simulator: Xyce DEVELOPMENT-202602210047

## Goal
- Validate the exact two-pass Middlebrook/Tian convention from the generic theory note using frequency-dependent grounded admittances.

## Setup
- Theory reference:
  - `docs/theories/loop_gain_analysis_middlebrook_tian.md`
- DUT:
  - `libs/exp_015_stb_theory/ideal_gm_go_gi_rc_cell.asdl`
- AC series pass:
  - `libs/exp_015_stb_theory/tb_ac_middlebrook_series.asdl`
- AC shunt pass:
  - `libs/exp_015_stb_theory/tb_ac_middlebrook_shunt.asdl`
- Parameters:
  - `Gm=1e-3 S`, `Go(s)=2e-4 + s*1p`, `Gi(s)=1e-4 + s*1p`

## Commands
```bash
RUN_ID=20260318T175450Z
RUN_DIR=runs/exp_015_stb_theory/${RUN_ID}

asdlc netlist libs/exp_015_stb_theory/tb_ac_middlebrook_series.asdl --backend sim.xyce -o ${RUN_DIR}/tb_ac_middlebrook_series.spice
asdlc netlist libs/exp_015_stb_theory/tb_ac_middlebrook_shunt.asdl --backend sim.xyce -o ${RUN_DIR}/tb_ac_middlebrook_shunt.spice

xyce ${RUN_DIR}/tb_ac_middlebrook_series.spice
xyce ${RUN_DIR}/tb_ac_middlebrook_shunt.spice

./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_ac_middlebrook_series.spice.raw
./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_ac_middlebrook_shunt.spice.raw

./venv/bin/python analysis/tools/xyce/analyze_middlebrook_ac_two_pass.py \
  ${RUN_DIR} --gm 1e-3 --go 2e-4 --gi 1e-4 --cout 1e-12 --cin 1e-12
```

## Artifacts
- run directory:
  - `runs/exp_015_stb_theory/20260318T175450Z`
- normalized outputs:
  - `runs/exp_015_stb_theory/20260318T175450Z/tb_ac_middlebrook_series.spice.raw.h5`
  - `runs/exp_015_stb_theory/20260318T175450Z/tb_ac_middlebrook_shunt.spice.raw.h5`
- analysis metrics:
  - `runs/exp_015_stb_theory/20260318T175450Z/metrics_middlebrook_ac_two_pass.json`

## Results
- Extracted equations used:
  - `Tv = -(Vr/Vf)` from series pass
  - `Ti = I(V_VS_OUT)/I(V_VS_IN)` from shunt pass
  - `1/(1+T) = 1/(1+Tv) + 1/(1+Ti)`
- Theory equations used:
  - `Tv_theory = (Gm+Gi(s))/Go(s)`
  - `Ti_theory = (Go(s)+Gm)/Gi(s)`
  - `T_theory = Gm/(Go(s)+Gi(s))`
- Numerical agreement:
  - `max_rel_err_Tv = 1.13e-15`
  - `max_rel_err_Ti = 8.87e-16`
  - `max_rel_err_T = 3.38e-13`
  - `max_abs_err(combine(Tv_theory,Ti_theory)-T_theory) = 2.22e-15`
- Unity crossing:
  - `UGB(T_measured) = 7.5912017198e7 Hz`
  - `UGB(T_theory) = 7.5912017198e7 Hz`

## Takeaway
- The same canonical convention validated in DC remains exact in AC for RC grounded admittances.
- Bench topology, signal mapping, and analyzer formulas are now aligned with theory and can be reused for more complex DUTs.

## Self-contained Reproduction
- Single-command runner:
  - `libs/exp_015_stb_theory/reproduce_exp015.sh`
- End-to-end (compile, simulate, normalize, analyze, and plot):
  - `libs/exp_015_stb_theory/reproduce_exp015.sh`
- Optional explicit run id:
  - `libs/exp_015_stb_theory/reproduce_exp015.sh 20260318T181407Z`
- Post-processing script (invoked by runner):
  - `libs/exp_015_stb_theory/postprocess_exp015.py`
