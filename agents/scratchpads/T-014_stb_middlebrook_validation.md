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

### Observations from AC1/AC2

- AC1 provides `I(V_VTEST)`, `V(OUT_SIDE)`, `V(INN_SIDE)`.
- AC2 currently provides only node voltages and no explicit current-sense branch for shunt source.
- Impedance-style combined candidates were degenerate (`Zo ~= Zc`), so no meaningful corrected loop-gain extraction yet.
- Current state still behaves like the Cload-only extraction path.

## Related work in exp013

- Added `ana.iac` and `libs_common/iprobe.asdl`
- Built OTA STB probes:
  - `libs/exp_013_ota5t_ac/tb_ac_stb_series.asdl`
  - `libs/exp_013_ota5t_ac/tb_ac_stb_shunt.asdl`
- Probe observables captured, but final robust two-run reconstruction equation not finalized.

## Key troubleshooting takeaway

Need a non-degenerate two-run probe formulation with explicit sensing of both injection and return variables, aligned with a strict Middlebrook/Tian equation. Current ad hoc two-pass GM setup is insufficient.

## Suggested next steps (next session)

1. Define exact target equation (Middlebrook or Tian form) and required measured quantities.
2. Refactor GM two-pass benches so AC2 includes explicit current sensing (e.g., 0 V sense source in shunt path).
3. Recompute loop gain from two-pass data and compare UGB against:
   - `gm/(2*pi*(cin+cload))` expected target,
   - `gm/(2*pi*cload)` current observed behavior.
4. Only after GM validation passes, port same method back to OTA exp013 benches.
