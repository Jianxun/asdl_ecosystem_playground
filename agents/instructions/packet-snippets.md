# Packet: Reusable Snippets

Copy-ready ASDL and command patterns for common lab tasks.

**Inject when:** Authoring a new testbench or analysis script.

## Minimal ngspice testbench imports

```yaml
imports:
  pdk: gf180mcu.asdl
  ana: analoglib.asdl
  sim: simulation.ngspice.asdl
  local_dut: ./dut.asdl   # same-directory DUT
```

## Minimal module shell

```yaml
modules:
  tb:
    instances: {}
    nets: {}
```

## Typical AC sources and analysis

```yaml
variables:
  VDD: 3.3
  VCM: 1.65

instances:
  vdd: ana.vdc dc={VDD}          # always use braces for variable substitution (pol-eb68439c)
  vss: ana.vdc dc=0
  ac_in: ana.vac dc={VCM} ac_mag=1 ac_phase=0

  ac1: sim.ac sweep_type=DEC points=100 start_freq=1 end_freq=1e9
  save1: sim.save sim_type=AC signals='V(*)'
```

## DC sweep with save

```yaml
instances:
  dc1: sim.dc vsrc=vsrc_in from=0 to=3.3 step=0.01
  save1: sim.save sim_type=DC signals='V(*)'   # sim_type required (les-200a5ad7)
```

## Canonical run loop (ngspice)

```bash
# 1. Sanity compile (no output flag)
asdlc netlist labs/builds/<lab-id>/asdl/tb.asdl --backend sim.ngspice

# 2. Emit netlist
asdlc netlist labs/builds/<lab-id>/asdl/tb.asdl --backend sim.ngspice -o labs/builds/<lab-id>/artifacts/tb.spice

# 3. Simulate
ngspice -b -o labs/builds/<lab-id>/artifacts/ngspice.log labs/builds/<lab-id>/artifacts/tb.spice

# 4. Normalize
./venv/bin/python analysis/tools/ngspice/normalize_raw.py \
  --input labs/builds/<lab-id>/artifacts/tb.raw \
  --output labs/builds/<lab-id>/artifacts/tb.hdf5

# 5. Plot
./venv/bin/python labs/builds/<lab-id>/scripts/plot_from_hdf5.py \
  --input labs/builds/<lab-id>/artifacts/tb.hdf5 \
  --out labs/builds/<lab-id>/figures
```

## Session telemetry queries

```bash
# Ingest and normalize latest sessions
./agents/scripts/run_opencode_ingestion.sh incremental

# Query session timeline (global flags before subcommand)
python3 agents/tools/opencode_session_pipeline/bin/history.py \
  --project playground timeline --session-id <ses_id>

# Query failed tools only
python3 agents/tools/opencode_session_pipeline/bin/history.py \
  --project playground tools --session-id <ses_id> --failed-only
```
