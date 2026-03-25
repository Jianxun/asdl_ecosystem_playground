# ASDL Labs Curriculum

Living table-of-contents and planning map for teaching labs.

This file is intentionally persistent and revision-friendly: labs can be reordered, expanded, split, or revised when quality standards are not met.

## Purpose

- Track planned and published labs in one place.
- Keep sequencing intentional (foundations -> intermediate -> advanced).
- Record revision intent when a lab needs quality upgrades.

## Quality gate (for publish-ready labs)

A lab is considered publish-ready only when it meets all of the following:

- Uses the required structure in `agents/prompts/workflows/lab.md`.
- Includes theory-first explanation and quantitative theory-vs-simulation comparison.
- Demonstrates a meaningful circuit property or design tradeoff.
- Is reproducible from repo root with explicit commands and paths.
- Includes script-generated figures and a complete `lab.md`.

## Status legend

- `planned`: scoped but not authored yet
- `drafting`: assets in progress
- `review`: technical/pedagogical review in progress
- `published`: meets quality gate
- `revise`: published once but currently below desired standard

## Curriculum roadmap

| ID | Title | Concept | Key Tradeoff/Property | Difficulty | Status | Notes |
|---|---|---|---|---|---|---|
| lab-01-rc-lowpass | RC Low-Pass Fundamentals | 1st-order filtering | cutoff frequency vs settling speed | beginner | review | canonical first lab |
| lab-02-resistive-divider-loading | Loaded Voltage Divider | source/load interaction | accuracy vs output drive | beginner | planned | introduce loading error |
| lab-03-common-source-gain-headroom | Common-Source Gain Stage | small-signal gain | gain vs output swing/headroom | intermediate | planned | include bias point sensitivity |
| lab-04-differential-pair-tail-current | Differential Pair Basics | transconductance steering | gain/linearity vs tail current | intermediate | planned | connect to OTA intuition |
| lab-05-current-mirror-compliance | Current Mirror Behavior | bias transfer | output resistance/compliance tradeoff | intermediate | planned | include finite ro effects |
| lab-06-two-stage-ota-stability | Two-Stage OTA Stability | loop compensation | phase margin vs bandwidth | advanced | planned | link to Middlebrook-style checks |

## Revision backlog

Use this section for labs in `revise` status.

| ID | Why revise | Target improvements | Owner | Target date |
|---|---|---|---|---|
| (none) | - | - | - | - |

## Change policy

- Preserve lab IDs once published; avoid renaming IDs unless migration is documented.
- If scope changes materially, update both this curriculum and lab `metadata.yaml`.
- When moving a lab to `revise`, include a concrete reason and expected fixes.
