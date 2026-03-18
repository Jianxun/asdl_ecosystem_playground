# P-005 Sign Conventions and Formulas

## Intent

Make measurement orientation and loop-gain formulas explicit to avoid silent sign errors.

## Why

- Small orientation changes can invert phase or alter loop-gain expressions.
- Reproducibility depends on stable conventions.

## Rules

- Document probe/source polarity and current direction.
- Document exact formula used for derived quantities (for example loop gain from node voltages).
- Include low-frequency sanity checks in analysis output (expected sign, expected magnitude order).
- If changing probe wiring, update formula documentation in same change.

## Required Metadata in Results

- Formula string used.
- Signal names used in formula.
- Orientation assumptions.
