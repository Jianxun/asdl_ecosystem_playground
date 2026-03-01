# Reusable Snippets

Use these as starting points; adapt per experiment.

## Minimal XYCE testbench imports

```yaml
imports:
  pdk: gf180mcu.asdl
  ana: analoglib.asdl
  sim: simulation.xyce.asdl
```

## Minimal module shell

```yaml
modules:
  tb:
    instances: {}
    nets: {}
```

## Typical sources + analyses

```yaml
instances:
  vdd: ana.vdc dc=3.3
  vss: ana.vdc dc=0
  ac_in: ana.vac dc=1.65 ac_mag=1 ac_phase=0

  ac1: sim.ac sweep_type=DEC points=100 start_freq=1 end_freq=1e9
  save1: sim.save_dc signals='V(*)'
```

## Output normalization commands

```bash
./venv/bin/python analysis/tools/xyce/raw_to_h5.py <run_dir>/tb.spice.raw
./venv/bin/python analysis/tools/xyce/format_xyce_op_csv.py <run_dir>/tb.spice.FD.prn
```

## Directory convention

```text
libs/<experiment_name>/
runs/<experiment_name>/<run_id>/
docs/<experiment_name>_<date>.md
```
