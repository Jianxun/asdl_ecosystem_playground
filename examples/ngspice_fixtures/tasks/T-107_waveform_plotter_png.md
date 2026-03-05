# T-107 — Implement waveform plotter and validate PNG output

## Objective
Build `tools/plot_waveforms.py` to render waveform plots from normalized HDF5 and save PNG files.

## Scope
- CLI args: input h5, signal(s), output path, title/style options.
- Use matplotlib.
- Handle missing signals with clear errors.
- Add minimal tests or smoke validation script.

## DoD
- Generates PNG for at least two fixture cases.
- README includes example commands.
- Repo-local `.venv` install notes remain valid.
