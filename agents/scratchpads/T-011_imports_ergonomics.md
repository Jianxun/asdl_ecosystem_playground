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

## Patch summary
- Pending.

## PR URL
- Pending.

## Verification
- Pending.

## Status request (Done / Blocked / In Progress)
- In Progress.

## Blockers / Questions
- None.

## Next steps
- Implement experiment sources and run verification.
