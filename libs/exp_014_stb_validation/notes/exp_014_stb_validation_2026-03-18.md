# Experiment Report: EXP-014 STB/Middlebrook Validation (Ideal GM Cell)

## Metadata
- id: exp_014_stb_validation
- date: 2026-03-18
- owner: OpenCode agent session with user guidance
- backend: sim.xyce
- simulator: Xyce DEVELOPMENT-202602210047

## Goal
- Validate two-pass loop-gain extraction (Middlebrook/STB style) on a deterministic ideal `gm-ro-cin` fixture where expected bandwidth is known.
- Verify whether combined voltage/current return-ratio reconstruction shifts bandwidth from `gm/(2*pi*cload)` toward `gm/(2*pi*(cin+cload))`.

## Setup
- DUT: `libs/exp_014_stb_validation/ideal_gm_cell.asdl`
  - `gm = 1e-3`, `ro = 100k`, `cin = 1p`
  - final topology uses grounded input caps:
    - `cin_inp: inp -> vss`
    - `cin_inn: inn -> vss`
- Load: `cload = 1p`
- AC sweep: `DEC`, `200` points/dec, `1 Hz` to `1e11 Hz`
- Expected references:
  - `f_ugb_cload = gm/(2*pi*cload) = 1.5915494309e8 Hz`
  - `f_bw_closed_loop = (gm+1/ro)/(2*pi*(cin+cload)) = 8.0373246261e7 Hz`

## Detailed Injection and Measurement Methods

### AC1 (series voltage injection)
- Bench: `libs/exp_014_stb_validation/tb_ac_unity_gm_middlebrook_ac1.asdl`
- Injection wiring:
  - `vtest: ana.vac ac_mag=1` placed between `out_side` and `inn_side`
  - `itest: ana.iac ac_mag=0` disabled in this run
  - `vinp` muted (`ac=0`)
- Saved observables:
  - `V(OUT_SIDE)`, `V(INN_SIDE)`, `I(V_VTEST)`
- Voltage return-ratio expression used:
  - `Tv = -V(OUT_SIDE)/V(INN_SIDE) - 1`

### AC2 (shunt current injection)
- Final bench: `libs/exp_014_stb_validation/tb_ac_unity_gm_middlebrook_ac2.asdl`
- Injection wiring (corrected):
  - `vshort: ana.vdc dc=0` shorts `out_side` to `inn_side`
  - `itest: ana.iac ac_mag=1` injects shunt current via `inj_n`
  - `vsense: ana.vdc dc=0` to ground provides explicit current readout (`I(V_VSENSE)`)
- Saved observables:
  - `I(V_VSENSE)`, `I(V_VSHORT)`, `V(INJ_N)`, `V(INN_SIDE)`, `V(OUT_SIDE)`
- KCL-derived DUT-side current:
  - `I_dut = -(I(V_VSENSE) + I(V_VSHORT))`
- Current return-ratio definition requested and used:
  - `Ti_user = I(V_VSHORT)/I_dut`

### Combined loop-gain equation
- Combined equation used per review:
  - `1/(1+T) = 1/(1+Tv) + 1/(1+Ti)`
- Analyzer reports both current-ratio conventions:
  - `Ti_user = I(V_VSHORT)/I_dut`
  - `Ti_inverse = I_dut/I(V_VSHORT)`

### Canonical handoff conventions (final for next session)
- Voltage return ratio:
  - `Tv = -(Vr/Vf)`
  - `Vr = V(OUT_SIDE)` from AC1
  - `Vf = V(INN_SIDE)` from AC1
- Current return ratio:
  - `Ti = -(Ir/If)`
  - `Ir = I(V_VSHORT)` from AC2
  - `If = I_dut` from AC2 KCL
  - `I_dut = -(I(V_VSENSE) + I(V_VSHORT))`
- Overall return ratio definition:
  - `1 + T = Tv + Ti`
  - `T = Tv + Ti - 1`
- Current orientation convention:
  - Xyce branch current `I(V_x)` is positive from source `p -> n` pin order in the ASDL netlist.

## Runs and Artifacts
- Open-loop sanity run with expected crossing: `runs/exp_014_stb_validation/20260318T013832Z`
- Single-pass series-voltage loop run: `runs/exp_014_stb_validation/20260318T015142Z`
- First two-pass attempt (missing AC2 current sense): `runs/exp_014_stb_validation/20260318T022418Z`
- Two-pass with explicit sense but wrong AC2 topology: `runs/exp_014_stb_validation/20260318T031655Z`
- Final corrected two-pass run: `runs/exp_014_stb_validation/20260318T033626Z`
- Post-DUT-topology correction run (grounded `cin`): `runs/exp_014_stb_validation/20260318T041325Z`

Generated analysis helpers:
- Signal inspection: `analysis/tools/xyce/inspect_xyce_signals.py`
- Two-pass metrics: `analysis/tools/xyce/analyze_middlebrook_two_pass.py`
- Canonical Tv/Ti extraction: `analysis/tools/xyce/extract_middlebrook_tv_ti.py`

Final run outputs:
- `runs/exp_014_stb_validation/20260318T041325Z/signals_manifest.json`
- `runs/exp_014_stb_validation/20260318T041325Z/metrics_middlebrook_two_pass.json`
- `runs/exp_014_stb_validation/20260318T041325Z/metrics_middlebrook_tv_ti.json`
- `runs/exp_014_stb_validation/20260318T041325Z/curves_middlebrook_tv_ti.csv`

## Key Results
- Open-loop sanity (`20260318T013832Z`):
  - DC gain ~ `100 V/V`
  - UGB ~ `1.5914698466e8 Hz` (matches `gm/(2*pi*cload)` within ~0.005%)
- Direct closed-loop reference after DUT correction (`20260318T041325Z`):
  - DC gain ~ `0.9901`
  - `f3dB ~ 8.0373130754e7 Hz` (matches `(gm+1/ro)/(2*pi*(cin+cload))`)
- AC1 voltage ratio (`Tv`) (`20260318T041325Z`):
  - `UGB(Tv) = 1.5755535479e8 Hz`
  - error vs `gm/(2*pi*cload)`: `-1.01%`
- AC2 corrected shunt behavior (`20260318T041325Z`):
  - `Ti_user(1e8 Hz) = 0.2790 + j0.4485`
  - `I_dut(1e8 Hz) = 0.6962 - j0.2441` (non-zero, frequency-dependent)
- Combined equation outcome (`20260318T041325Z`):
  - using `Ti_user`: no unity crossing
  - using `Ti_inverse`: `UGB = 8.5909713267e7 Hz`
  - error vs `(gm+1/ro)/(2*pi*(cin+cload))`: `+6.89%`
- Canonical Tv/Ti script output (`Tv=-(Vr/Vf)`, `Ti=-(Ir/If)`, `1+T=Tv+Ti`):
  - `Tv` unity crossing: none in sweep (`|Tv| > 1`)
  - `Ti` unity crossing: none in sweep (`|Ti| < 1`)
  - `T` unity crossing: none in sweep
  - `1+T` unity crossing: `2.8867370561e8 Hz`

## What We Tried, What Worked, What Did Not

Worked:
- Deterministic fixture validation (open-loop gain and pole behavior) matched theory.
- AC1 series voltage-injection method gave stable, repeatable `Tv` and UGB near the cload-only target.
- Adding reusable signal introspection (`inspect_xyce_signals.py`) quickly exposed missing observables.
- Correcting AC2 to shunt-to-ground injection produced physically meaningful current split and non-zero inferred DUT current.

Did not work (or gave degenerate/non-final results):
- Initial AC2 bench had no explicit injection current observable, so two-pass reconstruction was underdetermined.
- AC2 configuration with injection effectively across the same shorted loop produced trivial current behavior and no correction.
- Product-style combine attempts (for example `Tv * current_ratio`) did not recover expected `(cin+cload)` bandwidth.
- With the final combined equation, `Ti_user` convention did not produce a unity crossing; only reciprocal convention produced a plausible crossing.

## Reproducible Commands (final corrected run)
```bash
RUN_ID=20260318T041325Z
RUN_DIR=runs/exp_014_stb_validation/${RUN_ID}

asdlc netlist libs/exp_014_stb_validation/tb_ac_openloop_gm.asdl --backend sim.xyce -o ${RUN_DIR}/tb_ac_openloop_gm.spice
asdlc netlist libs/exp_014_stb_validation/tb_ac_unity_gm.asdl --backend sim.xyce -o ${RUN_DIR}/tb_ac_unity_gm.spice
asdlc netlist libs/exp_014_stb_validation/tb_ac_unity_gm_middlebrook_ac1.asdl --backend sim.xyce -o ${RUN_DIR}/tb_ac_unity_gm_middlebrook_ac1.spice
asdlc netlist libs/exp_014_stb_validation/tb_ac_unity_gm_middlebrook_ac2.asdl --backend sim.xyce -o ${RUN_DIR}/tb_ac_unity_gm_middlebrook_ac2.spice
asdlc netlist libs/exp_014_stb_validation/tb_ac_unity_gm_vtest.asdl --backend sim.xyce -o ${RUN_DIR}/tb_ac_unity_gm_vtest.spice

xyce ${RUN_DIR}/tb_ac_openloop_gm.spice
xyce ${RUN_DIR}/tb_ac_unity_gm.spice
xyce ${RUN_DIR}/tb_ac_unity_gm_middlebrook_ac1.spice
xyce ${RUN_DIR}/tb_ac_unity_gm_middlebrook_ac2.spice
xyce ${RUN_DIR}/tb_ac_unity_gm_vtest.spice

./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_ac_openloop_gm.spice.raw
./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_ac_unity_gm.spice.raw
./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_ac_unity_gm_middlebrook_ac1.spice.raw
./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_ac_unity_gm_middlebrook_ac2.spice.raw
./venv/bin/python analysis/tools/xyce/raw_to_h5.py ${RUN_DIR}/tb_ac_unity_gm_vtest.spice.raw

./venv/bin/python analysis/tools/xyce/inspect_xyce_signals.py ${RUN_DIR} -o ${RUN_DIR}/signals_manifest.json
./venv/bin/python analysis/tools/xyce/analyze_middlebrook_two_pass.py ${RUN_DIR} --gm 1e-3 --cin 1e-12 --cload 1e-12
./venv/bin/python analysis/tools/xyce/extract_middlebrook_tv_ti.py ${RUN_DIR} --csv ${RUN_DIR}/curves_middlebrook_tv_ti.csv
```

## Tooling Notes
- Diagnostics quality:
  - Signal-manifest generation materially reduced trial-and-error when checking whether AC2 had the required branch currents.
- Workflow friction:
  - The dominant friction was not simulator failure but ambiguity in probe orientation and return-ratio sign/reciprocal convention.
- Suggested fixes:
  - Pin down one normative `Ti` orientation in instructions and encode it directly in bench comments and analyzer docs.
  - Add a small "orientation self-check" in the analyzer (for example low-frequency expected sign/magnitude sanity assertions).
