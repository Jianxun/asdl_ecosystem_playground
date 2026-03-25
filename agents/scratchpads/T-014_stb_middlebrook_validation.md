# T-014 Scratchpad: STB/Middlebrook Validation on Ideal GM Cell

## Goal

Validate loop-gain extraction method (Middlebrook/STB style) against a deterministic first-order reference where theory is known.

## Deterministic reference circuit

- New primitive added: `ana.vccs` in `libs_common/analoglib.asdl`
- Ideal DUT module: `libs/exp_014_stb_validation/ideal_gm_cell.asdl`
  - Parameters: `gm`, `ro`, `cin`
  - Output path: VCCS + finite `ro`
  - Input cap: differential `cin` between `inp` and `inn`

## Open-loop sanity checks completed

- Testbench: `libs/exp_014_stb_validation/tb_ac_openloop_gm.asdl`
- Configuration used for visible UGB crossing:
  - `gm=1e-3`, `ro=100k`, `cin=1p`, `cload=1p`
  - AC sweep to `1e9`
- Results matched theory:
  - DC gain = `gm*ro = 100 V/V` (40 dB)
  - UGB ~ `gm/(2*pi*cload) = 1.5915e8 Hz` (sim ~ `1.59147e8 Hz`, ~0.005% error)

## Unity feedback with series voltage test source

- TB: `libs/exp_014_stb_validation/tb_ac_unity_gm_vtest.asdl`
  - `vinp` muted (`ac=0`)
  - `vtest` inserted between `dut.out` and `dut.inn`
  - measured nodes: `V(OUT_SIDE)`, `V(INN_SIDE)`
- Run: `runs/exp_014_stb_validation/20260318T015142Z`
- Working expression from this setup:
  - `T = -V(OUT_SIDE)/V(INN_SIDE) - 1`
- Observed UGB from that expression ~ `1.5755e8 Hz`
  - close to `gm/(2*pi*cload)`
  - does **not** show expected `gm/(2*pi*(cin+cload))`

## Two-pass attempt (ac1/ac2) for Middlebrook combination

- AC1 TB: `libs/exp_014_stb_validation/tb_ac_unity_gm_middlebrook_ac1.asdl`
  - `vtest ac=1`, `itest ac=0`
- AC2 TB: `libs/exp_014_stb_validation/tb_ac_unity_gm_middlebrook_ac2.asdl`
  - `vtest` replaced with `idc dc=0` (series branch opened for AC)
  - `itest ac=1`
- Latest run: `runs/exp_014_stb_validation/20260318T022418Z`

## AC2 refactor with explicit current sensing (new)

- Updated bench: `libs/exp_014_stb_validation/tb_ac_unity_gm_middlebrook_ac2.asdl`
  - Added `vshort: ana.vdc dc=0` for explicit shorted-port condition.
  - Added `vsense: ana.vdc dc=0` in series with shunt injector to expose `I(V_VSENSE)`.
- New two-pass run: `runs/exp_014_stb_validation/20260318T031655Z`
- Signal manifest (via helper tool): `runs/exp_014_stb_validation/20260318T031655Z/signals_manifest.json`
  - AC1: `I(V_VTEST)` + node voltages.
  - AC2: `I(V_VSENSE)`, `I(V_VSHORT)`, node voltages.

### New diagnostic insight

- With explicit short in AC2, `V(OUT_SIDE)-V(INN_SIDE)` is identically 0 by construction.
- Therefore shunt-run impedance forms (`Vport/Iinj`) are invalid/degenerate.
- AC2 must be consumed with a current-ratio form (using `I(V_VSENSE)` and `I(V_VSHORT)` / return current), not a voltage-over-current form.

## AC1+AC2 combined ratio check (new)

- Analysis script added: `analysis/tools/xyce/analyze_middlebrook_two_pass.py`
  - Inputs: run directory containing AC1/AC2 `.raw.h5`
  - Output: `metrics_middlebrook_two_pass.json`
  - Current formulas:
    - `T_ac1 = -V(OUT_SIDE)/V(INN_SIDE) - 1`
    - `R_current = -I(V_VSHORT)/I(V_VSENSE)`
    - `T_combined = T_ac1 * R_current`
- Result on `runs/exp_014_stb_validation/20260318T031655Z`:
  - `R_current` is exactly ~`1+0j` at 1 Hz and 1e8 Hz.
  - `UGB(T_ac1)` = `1.5755535e8 Hz`.
  - `UGB(T_combined)` = `1.5755535e8 Hz` (unchanged).
  - Theory references:
    - `gm/(2*pi*cload) = 1.5915494e8 Hz`
    - `gm/(2*pi*(cin+cload)) = 7.9577472e7 Hz`
- Conclusion: this current-ratio form is non-informative for correction in the present AC2 topology; combined metric still matches Cload-only behavior.

## AC2 topology correction: shunt injection to ground (new)

- Root cause fix applied in `libs/exp_014_stb_validation/tb_ac_unity_gm_middlebrook_ac2.asdl`:
  - `itest` moved to shunt orientation (injection referenced to ground through `vsense`), not across `out_side`/`inn_side`.
  - `vshort` retained only as the AC short between `out_side` and `inn_side`.
- New run: `runs/exp_014_stb_validation/20260318T033626Z`
- AC2 now shows non-trivial current split:
  - at `1e8 Hz`, `I(V_VSHORT) = 0.3038 + j0.2441` (normalized to `I(V_VSENSE)` sign convention in script)
  - inferred DUT-side port current from KCL is non-zero and frequency-dependent.
- Script-computed current return ratio and combination:
  - `I_dut = -(I(V_VSENSE)+I(V_VSHORT))` (KCL)
  - `R_current = I(V_VSHORT)/I_dut`
  - `UGB(T_ac1) = 1.5756e8 Hz`
  - `UGB(T_combined = T_ac1 * R_current)`: no unity crossing (stays < 1 in this formulation)
- Interpretation: corrected AC2 excitation is now physically meaningful; remaining issue is choosing the strict final combine equation/sign convention (product used above is not yet the target reconstruction).

## Combined equation update (new)

- Adopted equation per review:
  - `1/(1+T) = 1/(1+Tv) + 1/(1+Ti)`
- In analyzer (`analysis/tools/xyce/analyze_middlebrook_two_pass.py`), both Ti conventions are reported:
  - `Ti_user = I(V_VSHORT)/I_dut` (as stated from KCL definition)
  - `Ti_inverse = I_dut/I(V_VSHORT)` (reciprocal convention)
- For run `runs/exp_014_stb_validation/20260318T033626Z`:
  - `UGB(Tv)` = `1.5756e8 Hz`
  - `UGB(T_combined using Ti_user)` = no unity crossing
  - `UGB(T_combined using Ti_inverse)` = `8.5910e7 Hz`
    - closer to expected `gm/(2*pi*(cin+cload)) = 7.9577e7 Hz` than Cload-only value.

## DUT topology correction (final update)

- Updated `libs/exp_014_stb_validation/ideal_gm_cell.asdl`:
  - replaced differential `cin` branch with grounded caps:
    - `cin_inp: inp -> vss`
    - `cin_inn: inn -> vss`
- New consolidated rerun with corrected DUT: `runs/exp_014_stb_validation/20260318T041325Z`
- Direct closed-loop reference (`tb_ac_unity_gm`) now gives:
  - `f3dB ~ 8.0373e7 Hz`, matching `(gm+1/ro)/(2*pi*(cin+cload))`

## Canonical conventions for next session

- Voltage return ratio:
  - `Tv = -(Vr/Vf)`
  - `Vr = V(OUT_SIDE)` from AC1
  - `Vf = V(INN_SIDE)` from AC1
- Current return ratio:
  - `Ti = -(Ir/If)`
  - `Ir = I(V_VSHORT)` from AC2
  - `If = I_dut`, with `I_dut = -(I(V_VSENSE)+I(V_VSHORT))`
- Overall return ratio:
  - `1 + T = Tv + Ti`
  - `T = Tv + Ti - 1`

## New helper for canonical Tv/Ti extraction

- Added script: `analysis/tools/xyce/extract_middlebrook_tv_ti.py`
  - writes JSON metrics and optional CSV curves
  - default output: `<run_dir>/metrics_middlebrook_tv_ti.json`
- Latest artifacts:
  - `runs/exp_014_stb_validation/20260318T041325Z/metrics_middlebrook_tv_ti.json`
  - `runs/exp_014_stb_validation/20260318T041325Z/curves_middlebrook_tv_ti.csv`

### Historical note (early failed attempt)

- The first two-pass attempt (`runs/exp_014_stb_validation/20260318T022418Z`) lacked AC2 current sensing and was degenerate.
- This is now superseded by the corrected AC2 topology and canonical conventions above.

## Related work in exp013

- Added `ana.iac` and `libs_common/iprobe.asdl`
- Built OTA STB probes:
  - `libs/exp_013_ota5t_ac/tb_ac_stb_series.asdl`
  - `libs/exp_013_ota5t_ac/tb_ac_stb_shunt.asdl`
- Probe observables captured, but final robust two-run reconstruction equation not finalized.

## Key troubleshooting takeaway

Need a strict two-run equation that combines:

- AC1 series-run voltage/current observables (`Vport`, `I(V_VTEST)`), and
- AC2 shunt-run current observables (`I(V_VSENSE)`, `I(V_VSHORT)`),

with sign conventions explicitly fixed.

## Suggested next steps (next session)

1. Define exact target equation (Middlebrook or Tian form) and required measured quantities.
2. Refactor GM two-pass benches so AC2 includes explicit current sensing (e.g., 0 V sense source in shunt path).
3. Recompute loop gain from two-pass data and compare UGB against:
   - `gm/(2*pi*(cin+cload))` expected target,
   - `gm/(2*pi*cload)` current observed behavior.
4. Only after GM validation passes, port same method back to OTA exp013 benches.
