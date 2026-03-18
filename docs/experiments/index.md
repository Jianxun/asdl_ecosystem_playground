# Experiments Index

This index tracks completed and in-progress playground experiments with quick outcomes and pointers to primary notes.

| Experiment | Summary | Status | Outcome | Pointers |
|---|---|---|---|---|
| `exp_010_hello_xyce` | Bootstrapped the minimum ASDL -> Xyce -> normalization loop on a GF180 inverter. | done | End-to-end flow validated; first-run friction documented (`sim.save` usage, Python deps). | `libs/exp_010_hello_xyce/notes/exp_010_hello_xyce_2026-03-01.md`, `libs/exp_010_hello_xyce/` |
| `exp_011_imports` | Evaluated import ergonomics across `pdks/`, `libs_common/`, and local experiment files. | done | Compile/run path validated and import-style guidance captured. | `libs/exp_011_imports/notes/exp_011_imports_2026-03-01.md`, `libs/exp_011_imports/` |
| `exp_014_stb_validation` | Validated STB/Middlebrook extraction on an idealized fixture and debugged AC1/AC2 observability/convention issues. | done (investigation) | Reached a methodology roadblock and identified sign/orientation ambiguity as the key issue. | `libs/exp_014_stb_validation/notes/exp_014_stb_validation_2026-03-18.md`, `libs/exp_014_stb_validation/notes/exp_014_review.md`, `libs/exp_014_stb_validation/` |
| `exp_015_stb_theory` | Rebased loop-gain extraction with a generic `Gm-Go-Gi` theory model, then validated DC and AC two-pass benches against closed form. | done | Canonical `Tv/Ti` conventions now match theory with machine-precision agreement on the reference fixture. | `libs/exp_015_stb_theory/notes/exp_015_stb_theory_2026-03-18.md`, `libs/exp_015_stb_theory/notes/exp_015_stb_dc_two_pass_2026-03-18.md`, `libs/exp_015_stb_theory/notes/exp_015_stb_ac_two_pass_2026-03-18.md`, `docs/theories/loop_gain_analysis_middlebrook_tian.md`, `libs/exp_015_stb_theory/` |

## Notes

- `status=done (investigation)` means the experiment question was answered even if the answer was "current method is ambiguous and needs re-baselining".
- Prefer adding one new row per experiment ID and updating the same row as follow-up runs refine conclusions.
