# Experiment Report: EXP-015 STB/Middlebrook Theory Rebaseline

## Metadata
- id: exp_015_stb_theory
- title: Theory-first rebaseline for two-pass loop-gain extraction
- date: 2026-03-18
- owner: OpenCode agent session with user guidance
- backend: sim.xyce

## Question
- Which exact symbolic `Tv`, `Ti`, and combine equation should be treated as canonical for the ideal `gm-ro-cin` fixture, so bench topology/sign choices can be validated against a single ground truth?

## Setup
- Theory source path:
  - `libs/exp_015_stb_theory/theory_model.md`
- Derivation tool path:
  - `analysis/tools/xyce/derive_middlebrook_gm_theory.py`
- Parameter point used:
  - `gm=1e-3`, `ro=100k`, `cin=1p`, `cload=1p`

## Commands
```bash
RUN_ID=20260318T163124Z
RUN_DIR=runs/exp_015_stb_theory/${RUN_ID}

./venv/bin/python analysis/tools/xyce/derive_middlebrook_gm_theory.py \
  ${RUN_DIR} --gm 1e-3 --ro 100e3 --cin 1e-12 --cload 1e-12
```

## Artifacts
- run directory:
  - `runs/exp_015_stb_theory/20260318T163124Z`
- metrics:
  - `runs/exp_015_stb_theory/20260318T163124Z/metrics_middlebrook_theory.json`
- curves:
  - `runs/exp_015_stb_theory/20260318T163124Z/curves_middlebrook_theory.csv`

## Results
- Frozen closed-loop reference:
  - `H(s)=gm/(gm+go+s*(cin+cload))`
- Frozen true loop gain:
  - `T_true(s)=gm/(go+s*(cin+cload))`
- Frozen two-pass reconstruction:
  - `Tv(s)=(gm+s*cin)/(go+s*cload)`
  - `Ti(s)=(gm+go+s*cload)/(s*cin)`
  - `1/(1+T)=1/(1+Tv)+1/(1+Ti)`
- Algebraic conclusion:
  - This reconstruction gives `T(s)=T_true(s)` exactly for the ideal fixture.
- Numeric check at this parameter point:
  - `UGB(T_true) = 7.9573492507e7 Hz`
  - `UGB(T_combined from canonical Tv/Ti) = 7.9573492507e7 Hz`
  - `UGB(T_combined from legacy Tv) = 8.5909606415e7 Hz`
  - `max_abs_error(T_combined_canonical - T_true) = 5.73e-14`
- Practical implication for EXP-014 roadblock:
  - Using legacy `Tv = -(Vr/Vf)-1` introduces a systematic shift and reproduces the previously observed higher crossing (`~8.59e7 Hz`), while canonical `Tv=-(Vr/Vf)` aligns with the expected `~7.96e7 Hz` target.

## Ergonomics Findings
- What was easy:
  - Symbolic reduction of the ideal fixture isolates methodology errors from simulator details.
- What was confusing:
  - Mixing two `Tv` definitions (`-(Vr/Vf)` vs `-(Vr/Vf)-1`) can appear equivalent in notes but changes UGB materially.
- Time sinks / avoidable steps:
  - Re-running AC benches before freezing orientation and equation mapping.
- First-run friction:
  - first failing command: none
  - exact error text: n/a
  - fix applied: n/a
  - should update snippets/quickstart/debugging? (yes/no + where): yes; encode canonical STB equations in instructions/snippets before next AC2 bench iteration.

## Reusable Outputs
- script/tool updates:
  - `analysis/tools/xyce/derive_middlebrook_gm_theory.py`
- instruction updates:
  - `agents/instructions/snippets.md` (canonical two-pass equation note)

## Follow-ups
- immediate next experiment:
  - Build `exp_015` AC2 bench variant with explicit dual branch current sensing and a single frozen `Ti` orientation.
- tooling improvements to consider:
  - Add analyzer self-checks that reject legacy `Tv` usage and verify low-frequency asymptotes/KCL for AC2 current partitioning.
