# PROJECT STATUS

Last updated: 2026-03-26

## Milestones (Chronological)

### [x] M0 - Legacy Baseline (Issue: TBD)
- [x] Workflow authority established under `agents/`.
- [x] Core frictions identified: workflow sprawl, split guidance, path/terminology drift.

### [x] M1 - Strategic Recalibration (Issue: TBD)
- [x] Objective reset to harness hardening first.
- [x] Decision recorded: use `.agent/` as workflow control plane.

### [x] M2 - Control Plane Foundation (Issue: TBD)
- [x] Drafted `.agent/OBJECTIVE.md`.
- [x] Drafted `.agent/USER.md`.
- [x] Drafted `.agent/PROJECT_STATUS.md`.

### [ ] M3 - Objective-Aligned Workflow Design (Issue: TBD)
- [ ] Define minimal workflow set under `.agent/workflows/`.
- [ ] Define recommended testbench setup pattern and contracts.
- [ ] Define reusable helper-script contracts for compile/sim/normalize/analyze.
- [ ] Define `libs_common/` hardening rules.

### [ ] M4 - Documentation Consolidation (Issue: TBD)
- [ ] Publish user-guide style docs for canonical end-to-end loop.
- [ ] Unify active path conventions and terminology.
- [ ] Deprecate conflicting legacy guidance after replacement is proven.

### [ ] M5 - Capability Validation Loop (Issue: TBD)
- [ ] Run progressively harder circuit tasks with the hardened harness.
- [ ] Track friction deltas and turnaround time trends.
- [ ] Promote recurring fixes into workflows, libraries, and scripts.
- [ ] Repeat continuously (no terminal done state).

## Current Focus

- M3 - Objective-Aligned Workflow Design.

## Active Risks

- Dual-control-plane ambiguity (`agents/` and `.agent/`) during transition.
- Scope creep from broad migration before workflow contracts are rewritten.
- Inconsistent path conventions continuing to cause avoidable execution errors.

## Next Update Trigger

Update this file when a subtask checkbox changes, a milestone state changes, or a milestone-to-issue mapping is added/updated.
