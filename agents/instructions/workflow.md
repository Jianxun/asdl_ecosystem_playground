# Workflow

Canonical loop for ASDL Playground labs.

Execution policy and command conventions are defined in `playbook.md`.

## Intent

This is a playground for ergonomics and agent usability, not a conformance test suite.
Each lab should answer one practical question about authoring or tooling UX.

## Loop

1. **Define question**
   - Example: "How quickly can an agent author and run a parameterized AC testbench?"
2. **Author minimal ASDL**
   - Add/modify only what is needed to answer the question.
3. **Compile sanity check**
   - Run `asdlc netlist ... --backend sim.ngspice` first to catch authoring errors quickly.
4. **Compile to local artifact folder**
   - Emit netlist to `labs/<lab-id>/artifacts/tb.spice`.
5. **Simulate**
   - Run ngspice and collect raw outputs in `labs/<lab-id>/artifacts/`.
6. **Normalize**
   - Convert RAW to HDF5 using the canonical ngspice normalizer.
7. **Analyze**
   - Verify expected behavior and note friction.
8. **Distill**
   - Capture lessons, snippets, and workflow improvements.

## Required outputs per lab

- one source library under `labs/<lab-id>/`
- one local artifact set under `labs/<lab-id>/artifacts/`
- one lab write-up under `labs/<lab-id>/lab.md`
- one or more updates to `agents/instructions/` if new guidance emerges

## Scope control

- Prefer short, focused experiments over broad sweeps.
- Avoid introducing framework-level abstractions before two or more labs need them.
- When uncertain, choose explicit commands over hidden automation.
