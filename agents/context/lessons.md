# Lessons

## Pending additions
- Prefer self-contained lab artifacts under `labs/<lab-id>/artifacts/`; overwrite-in-place baseline is acceptable for now.
- Keep session telemetry archive at repo root `archive/` and out of git.
- Use `./agents/scripts/run_opencode_ingestion.sh` as the canonical ingestion entrypoint.
- For `history.py`, place global flags (`--project`, `--events-root`) before subcommands.

[T-010][executor]: Use `sim.save sim_type=<analysis>` for Xyce saves; `sim.save_dc` is not a valid primitive and fails compile.
[T-010][executor]: Add `h5py` to venv bootstrap checks because `raw_to_h5.py` depends on both `h5py` and `numpy`.
[T-010][executor]: Do a compile-only sanity pass before run-folder emission to catch ASDL symbol errors quickly.
[T-010][executor]: Keep run artifacts in `runs/<experiment>/<run_id>/` to make replay and report references deterministic.
[T-010][executor]: Repeated GF180 Xyce model warnings can be non-fatal; treat simulator exit code as the primary pass/fail signal.
[T-010][reviewer]: If scope ambiguity is explicitly resolved by the user in PR discussion, record that approval in review comments and proceed with closeout.
[T-011][executor]: For cross-library ASDL reuse, prefer `libs`-root-relative imports (for example `tb/tb_ota_5t/ota_nmos.asdl`) over `../` hops to keep paths stable during refactors.
[T-011][executor]: Xyce source primitives in emitted netlists may not accept symbolic `dc` values reliably in this flow; numeric literals are safer for voltage/current source setup.
[T-011][executor]: ASDL `modules.tb.variables` values substitute correctly for source parameters when referenced as `{VDD}`/`{VCM}`; unbraced symbols are emitted literally.
[T-011][executor]: `save_op` should emit `.PRINT DC FORMAT=CSV N(*)`; without `DC`, Xyce rejects the statement as analysis/print mismatch.
[T-016][review]: Event telemetry includes high-value friction signals from long/chained shell commands; these should be first-class heuristics in normalization output.
[T-016][review]: Not all `tool_failure` events are equally actionable; rank failures by diagnostic payload quality before promotion.
