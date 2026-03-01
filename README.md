# ASDL Playground

Experimental sandbox for practicing the ASDL workflow end to end:

1. Author circuits and testbenches in ASDL.
2. Compile with `asdlc` and inspect compile artifacts.
3. Run simulator backends and collect outputs.
4. Analyze results and capture repeatable guidance for future agents.

## Scope

- Fast iteration for language/tooling stress tests.
- Reproducible experiments with clear inputs/outputs.
- Documentation-first lessons that feed back into the ASDL ecosystem.

## Layout

- `libs/`: experiment libraries (one experiment per subdirectory).
- `libs_common/`: shared reusable ASDL blocks (sources, simulation helpers).
- `pdks/`: simulator/model infrastructure and PDK ASDL wrappers.
- `runs/`: generated netlists, logs, and simulation outputs (git-ignored).
- `analysis/`: metric extraction scripts and plots.
- `docs/`: experiment reports and guidance.
- `context/`: session memory and task tracking.
- `examples/`: legacy/reference assets (config/docs/scratch), not the primary authoring location.

## First Milestone

Establish one golden smoke experiment:

- ASDL source -> netlist emission -> simulator run -> metric extraction.
- Save an experiment report with command lines, artifacts, and findings.
