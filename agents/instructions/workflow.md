# Workflow

Canonical loop for ASDL Playground experiments.

## Intent

This is a playground for ergonomics and agent usability, not a conformance test suite.
Each experiment should answer one practical question about authoring or tooling UX.

## Loop

1. **Define question**
   - Example: "How quickly can an agent author and run a parameterized AC testbench?"
2. **Author minimal ASDL**
   - Add/modify only what is needed to answer the question.
3. **Compile sanity check**
   - Run `asdlc netlist ... --backend sim.xyce` first to catch authoring errors quickly.
4. **Compile to run folder**
   - Emit netlist to `runs/<experiment>/<run_id>/tb.spice` for reproducibility.
5. **Simulate**
   - Run Xyce and collect raw outputs in `runs/`.
6. **Normalize**
   - Convert outputs to analysis-friendly formats (HDF5 / pivoted CSV).
7. **Analyze**
   - Verify expected behavior and note friction.
8. **Distill**
   - Capture lessons, snippets, and workflow improvements.

## Required outputs per experiment

- one source library under `libs/<experiment_name>/`
- one reproducible run folder under `runs/<experiment_name>/<run_id>/`
- one report in `docs/`
- one or more updates to `agents/instructions/` if new guidance emerges

## Scope control

- Prefer short, focused experiments over broad sweeps.
- Avoid introducing framework-level abstractions before two or more experiments need them.
- When uncertain, choose explicit commands over hidden automation.
