# S-106 — Fix ngspice RAW normalization path to green E2E

## Objective
Resolve current E2E failure where ngspice fixture RAW format mismatches normalizer expectations.

## Scope
- Choose one robust path and implement end-to-end:
  1) emit ASCII RAW from fixtures, or
  2) add binary RAW support to normalizer.
- Ensure `scripts/e2e.py` succeeds through normalize/query/analyze stages.
- Keep tooling workflow-bound (no universal RAW parser ambition).
- Use repo-local venv only (`.venv/` under repo root).

## Out of Scope
- Xyce runtime support in this fix.
- Pole-zero fitting or new analyzer modules.

## Definition of Done (DoD)
- `python scripts/e2e.py --json` exits 0 in repo-local venv.
- Artifacts exist in `outputs/raw`, `outputs/hdf5`, and `outputs/analysis`.
- Brief fix note added to README with run command and venv usage.
