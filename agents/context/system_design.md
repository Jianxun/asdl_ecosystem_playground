# System Design: Self-Improving Agent Harness

This document captures the evolving design of the ASDL Playground harness. It is intentionally forward-looking and should be updated as the system matures.

## Core Thesis

If you have a physics-grounded oracle (a simulator), you can build a closed-loop system where an AI agent proposes, executes, observes outcomes, and improves — without requiring human labels. The simulator is the ground truth.

The labs and curriculum are the **training ground** for validating this loop. The dataset of sessions and telemetry is a **byproduct**. The compounding harness is the **product**.

## The Self-Improvement Loop

```
Author lab → Compile → Simulate → Normalize → Analyze → Explain
     ↑                                                        |
     └──── Promote lessons → Update harness ←── Extract signal
```

1. Agent produces a lab under the current harness rules.
2. Execution telemetry and user corrections are captured.
3. Friction, failures, and normative directives are extracted as structured policies and lessons.
4. Entries with sufficient evidence are promoted into prompts, instructions, and scripts.
5. The same lab task is rerun under the updated harness; telemetry delta confirms improvement.

The loop only compounds once step 5 is operational. Everything before that is setup.

## Two Session Tracks

### Track 1 — Interactive Sessions
- **Signal type:** Normative user language — "you should", "don't", "that's incorrect", "I want".
- **Signal quality:** Sparse but high-confidence. Direct correction = unambiguous ground truth.
- **Extraction:** Currently manual. Future: pattern-matched extraction pipeline.
- **Primary use:** Generates hypotheses about what to fix in the harness.

### Track 2 — Autonomous Sessions (dispatcher)
- **Signal type:** Execution telemetry — tool calls, failures, command complexity, phase tags.
- **Signal quality:** High volume, noisy. Requires heuristics to separate actionable from noise.
- **Extraction:** `normalize_events.py` pipeline (active, heuristics are a known gap).
- **Primary use:** Validates harness improvements quantitatively via rerun comparison.

**The natural flow:** Track 1 surfaces a directive → promoted to harness rule → Track 2 reruns the same task → telemetry delta confirms or rejects the improvement.

## Knowledge Store Design

### Goal

Feed proven priors into executor agent context windows in a targeted, evidence-backed way — without flooding context with irrelevant history.

### Two-Tier Model

Knowledge is split into two tiers with different lifecycles, stored as sibling directories:

```
agents/policies/     # Tier 1 — durable principles
agents/lessons/      # Tier 2 — time-scoped, expires when condition is met
agents/episodes/     # track records for both tiers (JSONL)
```

#### Tier 1 — Policies (`agents/policies/`)

Durable, permanent principles. Valid independent of specific bug states, tool versions, or codebase patches. A policy should survive a major library refactor unchanged.

**Gating question:** *Could this be resolved by fixing something in the codebase?* If yes, it belongs in the codebase, not here.

Examples:
- "Compile before emitting run folders to catch ASDL errors early."
- "Verify theory-vs-simulation within stated tolerance before closing a lab."
- "Keep artifacts local to `labs/<lab-id>/artifacts/`."

**Invalidation:** Only by explicit architectural decision.

#### Tier 2 — Lessons (`agents/lessons/`)

Time-scoped experiential knowledge. Valid under current conditions but tied to a known resolution condition — a bug fix, a library patch, a tool upgrade. Lessons are liabilities: they should pressure the team to fix the root cause.

**Promotion pathway:** If a lesson survives long enough without its expiry condition being met, it may reveal a deeper behavioral pattern worth promoting to a policy.

Examples:
- "Use `sim.save sim_type=<analysis>` for Xyce saves; `sim.save_dc` fails compile." *(expires when libs_common is patched)*
- "Xyce source primitives may not accept symbolic `dc` values; use numeric literals." *(expires on Xyce version upgrade)*

**Invalidation:** When `expires_when` condition is met, confirmed by a GC session.

### File Naming

IDs use a short content-derived hash (first 8 chars of SHA over content + created timestamp):

```
agents/policies/pol-3f8a2c1d.yaml
agents/lessons/les-9b4e7a02.yaml
agents/episodes/T-020-pol-3f8a2c1d.jsonl
```

The prefix (`pol-`, `les-`) makes the tier immediately clear from the ID alone.

### Policy Schema (YAML)

```yaml
id: pol-3f8a2c1d
content: "Compile before emitting run folders to catch ASDL errors early."
source:
  task: T-010
  track: 2           # 1=interactive, 2=autonomous
  session_id: ses_xxx

triggers:
  - field: phases    # match against ExecPlan/issue metadata fields
    pattern: "compile|simulate"

confidence: 0.7      # [0.0, 1.0]
status: active       # active | demoted | archived

stats:
  injection_count: 0
  success_count: 0   # injected; warned failure did NOT recur
  failure_count: 0   # injected; warned failure still recurred

created: 2026-03-25
```

### Lesson Schema (YAML)

Same as policy schema, with an additional `expires_when` block:

```yaml
id: les-9b4e7a02
content: "Use `sim.save sim_type=<analysis>`; `sim.save_dc` fails compile."
source:
  task: T-010
  track: 2
  session_id: ses_xxx

triggers:
  - field: backend
    pattern: "xyce"
  - field: phases
    pattern: "compile"

expires_when:
  condition: "sim.save_dc is a valid primitive in libs_common"
  watch: "libs_common/simulation.ngspice.asdl"  # file to check at GC time
  issue: null                                    # or GitHub issue tracking the fix

confidence: 0.6
status: active       # active | needs_review | demoted | archived

stats:
  injection_count: 0
  success_count: 0
  failure_count: 0

created: 2026-03-25
```

**Trigger fields** match against structured metadata in the ExecPlan or GitHub issue:
`backend`, `circuit_type`, `phases`, `tools`, `tags`.

Regex keeps retrieval auditable and simple. Embedding-based retrieval is deferred until the loop is proven.

### Episode Track Record (JSONL)

Each injection event and its outcome is one line in a JSONL file per entry:

```jsonl
{"kind": "injection", "id": "pol-3f8a2c1d", "task_id": "T-020", "session_id": "ses_yyy", "timestamp": "2026-03-25T10:00:00Z"}
{"kind": "outcome", "id": "pol-3f8a2c1d", "task_id": "T-020", "outcome": "success", "evidence": "No compile errors in phase.", "evaluated_at": "2026-03-26T09:00:00Z"}
```

Episode files are append-only. Written at two points:
1. **At ExecPlan creation** — architect injects entry, writes `injection` record.
2. **At review closeout** — reviewer writes `outcome` record.

### Confidence Scoring

Simple update rule applied after each outcome record is written:

| Event | Delta |
|---|---|
| Injected + failure did not recur | +0.1 |
| Injected + failure recurred | -0.2 |
| Not injected + failure occurred (retroactive) | +0.05 |

Thresholds:
- `confidence >= 0.8` → promote to **core** (always injected for matching tasks)
- `confidence < 0.3` → auto-demote to **demoted**
- Manual override always permitted

## Garbage Collection Sessions

Periodic Architect-role sessions with a narrow mandate — screen `agents/lessons/` for stale entries.

**Trigger:** After a significant library or tooling update, or after every N labs completed. Manual trigger for now.

**Steps:**
1. Scan `agents/lessons/` for entries where `expires_when.watch` file has changed or `expires_when.issue` is closed since `created`.
2. Flag affected entries as `needs_review`.
3. For each flagged entry: verify whether the root cause is resolved.
4. Decide: **archive** (fix landed), **promote to policy** (pattern is deeper than a bug), or **keep** (still valid, update evidence).
5. Spot-check `agents/policies/` entries with low confidence or no recent successful injections.

GC sessions do not execute labs. Read, evaluate, update only.

## Harness Injection Workflow

```
Architect creates ExecPlan
  → runs: agents/scripts/query_lessons.py --backend <x> --phases <y>
  → reviews matched policies + lessons ranked by confidence
  → injects selected entries into ExecPlan "Relevant Priors" section
  → appends injection records to agents/episodes/<id>.jsonl

Executor runs
  → reads ExecPlan including injected priors
  → executes task; telemetry captures tool calls, failures, corrections

Reviewer closes task
  → evaluates each injected entry against execution evidence
  → appends outcome records to agents/episodes/<id>.jsonl
  → confidence scores updated in policy/lesson YAML files
```

## Lab Pipeline

The lab pipeline has three stages with distinct artifact stability:

```
labs/specs/<lab-id>.yaml  ──[architect]──►  labs/plans/<lab-id>.md  ──[executor]──►  labs/builds/<lab-id>/
      (stable)                                  (regenerable)                            (regenerable)
```

**Spec** (`labs/specs/`) is the only artifact that never changes. It encodes the circuit
concept, theory checkpoint, required analyses, and acceptance criteria. It is the ground
truth against which plan and build quality are measured.

**Plans and builds** are regenerable. When the harness improves, the same spec can be
re-executed and output quality compared. This is the mechanism that makes the
self-improvement loop measurable.

Note: `agents/plans/` is reserved for general task ExecPlans (infra, tooling, migration).
`labs/plans/` is exclusively for lab pipeline plans.

Full evaluation criteria, metrics, and improvement attribution rules are in
`agents/context/lab_pipeline_evaluation.md`.

## Build Sequence

Priority order — prove the loop before optimizing it:

1. **Schema + directories** — create `agents/policies/`, `agents/lessons/`, `agents/episodes/`; migrate `agents/context/lessons.md` entries into appropriate tier.
2. **Retrieval script** — `agents/scripts/query_lessons.py` returns ranked matches from both tiers by trigger match.
3. **ExecPlan template update** — add `Relevant Priors` section to `agents/prompts/workflows/execplan.md`.
4. **Episode logging** — append injection records at ExecPlan creation; append outcome records at review closeout.
5. **Confidence scoring** — implement update logic after first full loop produces real episode data.
6. **GC session protocol** — document and run first GC session after a library update.
7. **Track 1 extraction** — pattern-match normative directives from interactive session logs to auto-generate candidates.
8. **Dynamic context injection** — runtime injection without architect mediation (deferred; requires proven loop first).

## What Is Not Being Built Yet

- Embedding-based semantic retrieval (regex is sufficient to prove the loop)
- Automated Track 1 directive extraction (currently manual)
- Dynamic runtime context injection
- Cross-project generalization (analog design first; other simulator-grounded domains later)

## Generalization Path

The pattern — simulator as oracle, telemetry as signal, policies/lessons as priors, rerun as validation — is not analog-specific. It applies to any domain with deterministic physics-grounded simulation:

- Structural FEA
- Thermal / fluid simulation
- RF / antenna design
- Power electronics
- Chemical process modeling

Analog design is the first instantiation. The harness is the generalizable artifact.
