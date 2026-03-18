# T-015 Scratchpad: STB/Middlebrook Theory Rebaseline

## Goal

Reset methodology from first principles and freeze a gold-standard symbolic reference for the ideal `gm-ro-cin` unity follower before more bench iterations.

## Why this experiment exists

- EXP-014 showed AC1 repeatedly landing near `gm/(2*pi*cload)`.
- AC2 became topology/sign-convention sensitive and did not produce a stable single canonical reconstruction.
- We need one unambiguous equation set to test bench observables against.

## Theory baseline (frozen)

For `go = 1/ro`, `cin` at the feedback node to ground, and `cload` at output to ground:

- Closed-loop transfer:
  - `H(s) = gm / (gm + go + s*(cin + cload))`
- True loop gain:
  - `T_true(s) = gm / (go + s*(cin + cload))`
- Expected unity-loop target:
  - `f_u ~= gm/(2*pi*(cin+cload))`

## Canonical two-pass equations (frozen)

- Voltage pass:
  - `Tv = -(Vr/Vf)` (not `-(Vr/Vf)-1`)
  - Ideal fixture reduction: `Tv(s) = (gm + s*cin)/(go + s*cload)`
- Current pass:
  - `Ti = -(Ir/If)` with branch orientation set so ideal reduction is:
  - `Ti(s) = (gm + go + s*cload)/(s*cin)`
- Combine:
  - `1/(1+T) = 1/(1+Tv) + 1/(1+Ti)`

These reduce algebraically to `T(s)=T_true(s)` exactly for this fixture.

## Key diagnosis from theory

- AC1 alone naturally tracks output-side loading and can look `cload`-dominated.
- Legacy `Tv = -(Vr/Vf)-1` biases reconstruction and shifts combined crossing upward.
- Canonical `Tv = -(Vr/Vf)` + canonical `Ti` orientation removes that bias.

## Artifacts created in T-015

- Theory source note:
  - `libs/exp_015_stb_theory/theory_model.md`
- Reproducible numeric derivation tool:
  - `analysis/tools/xyce/derive_middlebrook_gm_theory.py`
- Theory run artifacts:
  - `runs/exp_015_stb_theory/20260318T163124Z/metrics_middlebrook_theory.json`
  - `runs/exp_015_stb_theory/20260318T163124Z/curves_middlebrook_theory.csv`
- Report:
  - `docs/exp_015_stb_theory_2026-03-18.md`

## Next implementation step after theory lock

1. Build new AC2 bench with explicit branch current sensors on both sides of the original cut. (done in DC)
2. Map measured branch currents to `(Ir, If)` exactly as frozen above. (done in DC)
3. Remove dual-convention ambiguity from analyzers and keep one canonical `Ti` only. (done for DC analyzer)

## DC two-pass validation (resistive, no capacitors)

Implemented under `libs/exp_015_stb_theory/`:

- DUT: `ideal_gm_go_gi_cell.asdl`
- AC1-equivalent series testbench (DC): `tb_dc_middlebrook_series.asdl`
- AC2-equivalent shunt testbench (DC): `tb_dc_middlebrook_shunt.asdl`

Analyzer:

- `analysis/tools/xyce/analyze_middlebrook_dc_two_pass.py`

Run:

- `runs/exp_015_stb_theory/20260318T174956Z`

Measured (`gm=1e-3`, `go=2e-4`, `gi=1e-4`):

- `Tv = -Vr/Vf = 5.5` (theory `(Gm+Gi)/Go = 5.5`)
- `Ti = Iout/Iin = 12.0` (theory `(Go+Gm)/Gi = 12.0`)
- `T_combined = 3.3333333` (theory `Gm/(Go+Gi) = 3.3333333`)

Result: exact numeric agreement to solver precision on the pure-resistive baseline.

## AC two-pass validation (RC frequency-dependent case)

Implemented under `libs/exp_015_stb_theory/`:

- DUT with grounded RC admittances:
  - `ideal_gm_go_gi_rc_cell.asdl`
- AC series pass:
  - `tb_ac_middlebrook_series.asdl`
- AC shunt pass:
  - `tb_ac_middlebrook_shunt.asdl`

Analyzer:

- `analysis/tools/xyce/analyze_middlebrook_ac_two_pass.py`

Run:

- `runs/exp_015_stb_theory/20260318T175450Z`

Measured and theory-aligned formulas:

- `Tv = -(Vr/Vf)`
- `Ti = I(V_VS_OUT)/I(V_VS_IN)` (matches canonical `-(Ir/If)` with chosen sensor orientation)
- `1/(1+T)=1/(1+Tv)+1/(1+Ti)`

Key outcomes at `gm=1e-3, go=2e-4, gi=1e-4, cin=cout=1p`:

- `UGB(T_measured) = 7.5912017198e7 Hz`
- `UGB(T_theory) = 7.5912017198e7 Hz`
- `max_rel_err_Tv = 1.13e-15`
- `max_rel_err_Ti = 8.87e-16`
- `max_rel_err_T = 3.38e-13`

Result: AC two-pass reconstruction matches the generic theoretical expressions across the sweep.
