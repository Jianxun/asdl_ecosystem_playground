# P-005 Sign Conventions and Formulas

## Intent

Make measurement orientation and loop-gain formulas explicit to avoid silent sign errors.

## Why

- Small orientation changes can invert phase or alter loop-gain expressions.
- Reproducibility depends on stable conventions.

## Rules

- Document probe/source polarity and current direction.
- Document exact formula used for derived quantities (for example loop gain from node voltages).
- Freeze exactly one canonical formula/orientation set per analysis mode; avoid parallel "equivalent" conventions in one experiment.
- Include low-frequency sanity checks in analysis output (expected sign, expected magnitude order).
- Include reciprocal/consistency checks when ratios can be inverted by orientation (for example verify whether a measured ratio is the reciprocal of the intended theorem quantity).
- If changing probe wiring, update formula documentation in same change.

## Required Metadata in Results

- Formula string used.
- Signal names used in formula.
- Orientation assumptions.

## Example (non-normative)

- See `docs/theories/loop_gain_analysis_middlebrook_tian.md` for a transferable two-pass derivation pattern showing:
  - explicit symbol-to-signal mapping,
  - AC1/AC2 ratio definitions under fixed orientation,
  - algebraic reconstruction and sanity-limit checks.
