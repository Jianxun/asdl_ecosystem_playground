# T-011 — Evaluate import ergonomics with 5T OTA chain

## Task summary (DoD + verify)
- DoD: Build a 5-transistor OTA experiment (`ota_5t_op`) that explicitly imports from `libs_common/`, `libs/`, and `pdks/`. Document where agents hit import ambiguity and produce one import-style guideline update in `agents/instructions/`.
- Verify:
  - `./venv/bin/asdlc netlist libs/exp_011_imports/tb.asdl --backend sim.xyce`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`

## Plan
- Author `libs/exp_011_imports/` with a 5T OTA DUT and OP-oriented testbench.
- Use explicit imports that exercise `pdks/`, `libs_common/`, and `libs/` lookup paths.
- Run compile verification and record import ambiguity points.
- Update one import-style guideline under `agents/instructions/` and capture findings in `docs/`.

## Milestone notes
- Intake complete; task selected as ready.
- Set `T-011` to `in_progress` and passed `lint_tasks_state.py`.
- TDD compile-first check failed as expected before implementation (`PARSE-004` missing `libs/exp_011_imports/tb.asdl`).
- Implemented `ota_5t_op` wrapper that imports an OTA core from `libs/` (`tb/tb_ota_5t/ota_nmos.asdl`).
- Implemented testbench imports spanning all roots: `gf180mcu.asdl` (pdks), `analoglib.asdl` and `simulation.xyce.asdl` (libs_common), plus local DUT wrapper.
- Compile verification now passes for `libs/exp_011_imports/tb.asdl` on `sim.xyce`.
- Added import-style guidance to `agents/instructions/snippets.md` and captured ambiguity notes in `docs/exp_011_imports_2026-03-01.md`.
- Follow-up: made experiment self-contained by copying OTA source into `libs/exp_011_imports/ota_5t.asdl` and updating `tb.asdl` to use local imports only.
- Follow-up: ran `xyce libs/exp_011_imports/tb.spice`; first run failed on unresolved symbolic source values, then passed after replacing `VDD`/`VCM` with numeric literals.

## Patch summary
- Added experiment sources and compile artifacts:
  - `libs/exp_011_imports/ota_5t.asdl`
  - `libs/exp_011_imports/tb.asdl`
  - `libs/exp_011_imports/tb.spice`
  - `libs/exp_011_imports/tb.log.json`
  - `libs/exp_011_imports/tb.spice.raw`
- Added experiment report:
  - `docs/exp_011_imports_2026-03-01.md`
- Updated import guidance:
  - `agents/instructions/snippets.md`

## PR URL
- https://github.com/Jianxun/asdl_ecosystem_playground/pull/2

## Verification
- `./venv/bin/python agents/scripts/lint_tasks_state.py` -> pass
- `./venv/bin/asdlc netlist libs/exp_011_imports/tb.asdl --backend sim.xyce` (pre-implementation) -> expected fail (`PARSE-004` missing file)
- `./venv/bin/asdlc netlist libs/exp_011_imports/tb.asdl --backend sim.xyce` (post-implementation) -> pass
- `xyce libs/exp_011_imports/tb.spice` (follow-up run #1) -> fail (`Invalid DC value "VDD"/"VCM"`)
- `xyce libs/exp_011_imports/tb.spice` (follow-up run #2) -> pass

## Status request (Done / Blocked / In Progress)
- Ready for Review.

## Blockers / Questions
- None.

## Next steps
- Reviewer to validate import-style guidance and compile reproducibility.
