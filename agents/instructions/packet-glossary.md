# Packet: Glossary

Key terms used across ASDL Playground harness files.

**Inject when:** Needed for term clarification; otherwise low priority.

## Terms

- **ASDL**: the circuit description language used for design and testbench authoring.
- **Lab**: a self-contained teaching unit covering one circuit concept; canonical location `labs/<lab-id>/`.
- **Backend**: emitter target syntax/profile (e.g., `sim.ngspice`, `sim.xyce`).
- **PDK assets**: model and primitive definitions under `pdks/`.
- **Normalization**: converting raw simulator output (RAW) into consistent HDF5 format.
- **ExecPlan**: per-task execution plan document under `agents/plans/`; executor's primary working document.
- **Hydration packet**: one of the `packet-*.md` files in `agents/instructions/`; injected into agent context as needed.
- **Policy**: durable behavioral rule in `agents/policies/`; remains valid across code changes.
- **Lesson**: time-scoped experiential knowledge in `agents/lessons/`; has explicit expiry condition.
- **Episode**: injection + outcome record in `agents/episodes/`; JSONL append-only.
- **GC session**: Garbage Collection session — Architect-role review of `agents/lessons/` for stale entries.
- **Ergonomics issue**: anything that makes authoring/debugging slower, error-prone, or unclear.
- **Self-improvement loop**: the closed loop of labs → telemetry → lesson extraction → harness update → rerun.
