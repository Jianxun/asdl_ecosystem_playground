# S-107 — Waveform Plotter (HDF5 -> PNG)

## Objective
Create a plotting tool that reads normalized HDF5 waveforms and writes PNG figures suitable for sharing.

## Scope
- Implement `tools/plot_waveforms.py` CLI.
- Input: HDF5 file from normalizer.
- Signal selection: one or multiple signal names.
- Modes:
  - transient: y vs independent variable (time)
  - AC: gain/phase style optional, or generic y vs x fallback
- Output: PNG in `outputs/plots/` (configurable path).
- Optional style presets for readability.

## Out of Scope
- Interactive GUI.
- Advanced publication layouts.

## Definition of Done (DoD)
- Can generate PNG from fixture HDF5 artifacts.
- Works for at least transient and AC fixture cases.
- CLI usage documented in README.
