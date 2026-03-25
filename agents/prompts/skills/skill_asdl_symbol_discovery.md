# Skill: ASDL Symbol Discovery

## Purpose

Resolve ASDL imports/symbols quickly and reliably to avoid API guessing during authoring.

## Uses Principles

- `P-003` script-first analysis (tooling reuse)
- `P-008` close the loop on guidance

## Tools

- `scripts/asdl-member`
- `scripts/asdl-symbol`

## When to Use

- Unsure which `sim.*` primitive exists
- Unsure module/device params and ports
- Import alias resolution/debugging

## Workflow

1. **List alias members**
   - `venv/bin/python scripts/asdl-member <source.asdl> <alias> --json`
2. **Resolve exact symbol**
   - `venv/bin/python scripts/asdl-symbol <source.asdl> <alias.member> --json`
3. **Apply edit with known API**
   - use returned params/ports/definition location
4. **Compile check**
   - run `asdlc netlist ... --backend sim.xyce`

## Outputs to capture

- resolved symbol kind (`device`/`module`)
- ports and parameters/instances
- resolved import file path

## Troubleshooting

- alias not found: verify `imports:` block in source file
- symbol not found: run `asdl-member` first to enumerate valid names
- import resolution failure: verify `.asdlrc` `lib_roots` and local `./` paths
