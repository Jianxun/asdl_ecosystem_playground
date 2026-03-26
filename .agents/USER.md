# USER

This file stores stable facts and preferences for the project owner.

## User Facts

- User is the project owner and primary operator for this repository.
- User is intentionally repositioning this project toward workflow hardening.
- User wants `.agent/` to be the control plane and kept out of the main repo surface area.

## Strategic Preferences

- Prefer objective-driven redesign over naive migration/copying of legacy workflows.
- Prioritize practical user-guide documentation for ASDL workflows.
- Emphasize reusable assets (testbench patterns, shared libraries, helper scripts) over one-off task outputs.
- Build a harness that supports more challenging circuits without repeated tooling friction.

## Workflow Preferences

- Keep workflows focused and minimal; avoid unnecessary process bloat.
- Favor deterministic, root-runnable command paths.
- Keep cross-session continuity explicit in persistent control-plane files.
- Require changes to be justified by measurable friction reduction.

## Communication Preferences

- Collaborative tone with direct recommendations.
- Start with strategy and rationale before broad mechanical migration.
- Avoid unnecessary complexity and avoid adopting process for process' sake.

## Update Rules

- Add only durable preferences or facts that are likely to remain true across sessions.
- Do not store transient task state here (use `PROJECT_STATUS.md` for that).
- If a preference changes, update the entry in place instead of appending contradictory notes.
