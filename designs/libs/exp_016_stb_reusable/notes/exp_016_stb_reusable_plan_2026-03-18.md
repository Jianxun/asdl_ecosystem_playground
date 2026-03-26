# Experiment Plan: EXP-016 Reusable Two-Pass STB Orchestration

## Metadata
- id: exp_016_stb_reusable
- title: Single-source orchestration for two-pass loop-gain extraction
- date: 2026-03-18
- owner: OpenCode agent session with user guidance
- backend: sim.xyce

## Question
- Can we drive AC1/AC2 from one ASDL source file without hand-editing testbench files between runs, while preserving canonical `Tv/Ti` extraction?

## Recommended architecture
- Keep one source-of-truth ASDL file:
  - `libs/exp_016_stb_reusable/tb_ac_middlebrook_two_pass.asdl`
- Keep both pass topologies as separate modules inside that file:
  - `tb_series` for voltage return ratio (`Tv`)
  - `tb_shunt` for current return ratio (`Ti`)
- Use a small orchestration script to materialize per-pass ASDL files in `runs/` with parameterized source amplitudes:
  - series: `vtest_ac=1`, `itest_ac=0`
  - shunt: `vtest_ac=0`, `itest_ac=1`
- Compile/simulate both outputs and post-process with the existing canonical analyzer:
  - `analysis/tools/xyce/analyze_middlebrook_ac_two_pass.py`

## Why this is the current best default
- It gives a single editable bench source while avoiding fragile topology multiplexing in one module.
- It supports `vtest_ac`/`itest_ac` parameter control at run time without manual edits.
- It keeps existing validated AC1/AC2 equations, signal names, and analyzer compatibility.

## Next extension candidates
- Add a generic analyzer CLI that accepts explicit signal maps so it can be reused across non-ideal DUTs.
- Add optional self-checks that reject legacy `Tv=-(Vr/Vf)-1` in this workflow.
- If ASDL gains top/variable CLI overrides in `asdlc`, remove materialization and compile directly from one file.
