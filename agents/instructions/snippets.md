# Reusable Snippets

Use these as starting points; adapt per experiment.

Normative import policy lives in `playbook.md`; this file stays example-focused.

## Minimal XYCE testbench imports

```yaml
imports:
  pdk: gf180mcu.asdl
  ana: analoglib.asdl
  sim: simulation.xyce.asdl
```

## Import style example (T-011)

Example pattern to reduce ambiguity:

```yaml
imports:
  # From pdks/<pdk>/asdl or libs_common/ (resolved by lib_roots)
  pdk: gf180mcu.asdl
  ana: analoglib.asdl
  sim: simulation.xyce.asdl

  # Same directory as current file
  local_dut: ./ota_5t.asdl
```

For portability rationale and policy language, see `playbook.md`.

## Minimal module shell

```yaml
modules:
  tb:
    instances: {}
    nets: {}
```

## Typical sources + analyses

```yaml
variables:
  VDD: 3.3
  VCM: 1.65

instances:
  vdd: ana.vdc dc={VDD}
  vss: ana.vdc dc=0
  ac_in: ana.vac dc={VCM} ac_mag=1 ac_phase=0

  ac1: sim.ac sweep_type=DEC points=100 start_freq=1 end_freq=1e9
  save1: sim.save sim_type=AC signals='V(*)'
```

## Canonical DC save directive

```yaml
instances:
  dc1: sim.dc vsrc=vsrc_in from=0 to=3.3 step=0.01
  save_v: sim.save sim_type=DC signals='V(*)'
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

## Two-pass STB theory baseline (ideal gm fixture)

Use these equations when validating Middlebrook/Tian extraction on the ideal `gm-ro-cin` unity follower:

```text
Tv = -(Vr/Vf)
Ti = -(Ir/If)
1/(1+T) = 1/(1+Tv) + 1/(1+Ti)
```

Do not mix in the legacy `Tv = -(Vr/Vf)-1` form when using the equation above; it shifts reconstructed unity crossing.
