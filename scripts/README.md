# ASDL Helper Scripts

This folder contains lightweight helper scripts for ASDL symbol discovery.

## Prerequisites

- Python 3.10+
- `PyYAML` installed in your environment

Example using this repo venv:

```bash
venv/bin/python scripts/asdl-member --help
venv/bin/python scripts/asdl-symbol --help
```

## `asdl-member`

Lists members exported by an import alias in a source ASDL file.

### Usage

```bash
scripts/asdl-member <source.asdl> <alias> [--json]
```

### Example

```bash
venv/bin/python scripts/asdl-member libs/exp_010_hello_xyce/tb.asdl sim --json
```

### Output

- `alias`: import alias queried
- `import`: raw import target from source file
- `resolved_file`: resolved imported file path
- `devices`: exported device names
- `modules`: exported module names

## `asdl-symbol`

Resolves a qualified symbol (`alias.member`) from a source ASDL file.

### Usage

```bash
scripts/asdl-symbol <source.asdl> <alias.member> [--json]
```

### Examples

```bash
venv/bin/python scripts/asdl-symbol libs/exp_010_hello_xyce/tb.asdl sim.save --json
venv/bin/python scripts/asdl-symbol libs/exp_010_hello_xyce/tb.asdl inv.inv --json
```

### Output

Common fields:

- `query_file`, `symbol`, `alias`, `member`
- `import`, `resolved_file`
- `kind` (`device` or `module`)
- `line` (best-effort definition line)

Device fields:

- `ports`
- `parameters`

Module fields:

- `ports` (module ports inferred from `$...` net keys)
- `instances`

## Resolution behavior

- Local imports (`./...`, `../...`) resolve relative to the source file.
- Non-local imports resolve via `.asdlrc` `lib_roots` (with env expansion), then fallback roots:
  - `pdks/`
  - `libs_common/`
  - `libs/`
