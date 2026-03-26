# EXP-016: Reusable Two-Pass STB Runner

This experiment packages AC1/AC2 loop-gain extraction so both passes are generated from one ASDL source file.

## Source assets
- `tb_ac_middlebrook_two_pass.asdl`: single source-of-truth with `tb_series` and `tb_shunt` modules.
- `ideal_gm_go_gi_rc_cell.asdl`: ideal fixture used for validation.
- `run_exp016.py`: orchestration script that materializes pass-specific ASDL files into `runs/` and executes compile/sim/analyze.

## Default run

```bash
./venv/bin/python libs/exp_016_stb_reusable/run_exp016.py
```

## Example with explicit source amplitudes

```bash
./venv/bin/python libs/exp_016_stb_reusable/run_exp016.py \
  --series-vtest-ac 1 --series-itest-ac 0 \
  --shunt-vtest-ac 0 --shunt-itest-ac 1
```

Outputs are written to:

```text
runs/exp_016_stb_reusable/<run_id>/
```
