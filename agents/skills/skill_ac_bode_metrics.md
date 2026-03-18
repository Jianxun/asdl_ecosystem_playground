# Skill: AC Bode Metrics

## Purpose

Extract consistent AC gain/phase metrics from simulator outputs with clear formulas and sign conventions.

## Uses Principles

- `P-001` theory-simulation correlation
- `P-003` script-first analysis
- `P-005` sign conventions and formulas
- `P-007` experiment analysis recipe

## When to Use

- Open-loop gain characterization
- Closed-loop bandwidth extraction
- Candidate loop-gain reconstructions

## Workflow

1. **Run AC bench**
   - Use explicit sweep settings (`start`, `stop`, `points`)
2. **Normalize**
   - Convert RAW to HDF5
3. **Compute transfer function**
   - Define exact formula for `H(jw)` or `T(jw)`
   - Record signal names used
4. **Extract metrics**
   - `A0` at low frequency
   - `fp` (-3 dB corner or fit)
   - `UGB` from `|T|=1` crossing
   - phase at UGB and phase margin proxy if applicable
5. **Plot**
   - Bode magnitude/phase
   - mark crossing points
6. **Compare with theory**
   - include expected formulas and percent error

## Required Outputs

- `metrics_ac_*.json`
- Bode plot PNG(s)
- explicit formula string in metrics/summary

## Guardrails

- Ensure sweep extends far enough to include expected crossing.
- If no crossing exists, report as such (do not extrapolate silently).
- Validate sign orientation with low-frequency expectation.
