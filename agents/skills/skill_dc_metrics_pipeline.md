# Skill: DC Metrics Pipeline

## Purpose

Run DC-focused experiments with repeatable post-processing and reusable artifacts.

## Uses Principles

- `P-001` theory-simulation correlation
- `P-003` script-first analysis
- `P-005` sign conventions and formulas
- `P-007` experiment analysis recipe

## When to Use

- Differential I-V transfer benches
- Unity-gain DC tracking benches
- Bias/current sweep characterization

## Workflow

1. **Run bench**
   - Compile with `asdlc` to `runs/<exp>/<run_id>/...`
   - Simulate with `xyce`
2. **Normalize outputs**
   - `analysis/tools/xyce/raw_to_h5.py`
3. **Extract metrics (scripted)**
   - Use or create script in `analysis/tools/xyce/`
   - Emit `metrics_*.json`
4. **Generate plots (scripted)**
   - Emit `plot_*.png`
5. **Sanity checks**
   - low-frequency/low-input checkpoints
   - sign/orientation checks for currents
6. **Record recipe**
   - update experiment summary with commands, formulas, and expected ranges

## Required Outputs

- `metrics_*.json`
- at least one `plot_*.png`
- summary markdown with formulas and assumptions

## Common DC Metrics

- Differential I-V: plateau currents, zero crossing, `dI/dV` near zero
- Unity tracking: max `|Vout-Vin|`, linear region range, endpoint errors
- Sweep trends: scaling versus bias/load parameters
