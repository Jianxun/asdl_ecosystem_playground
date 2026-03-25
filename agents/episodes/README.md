# Episodes

Append-only JSONL track records for policy and lesson injections.

One file per policy/lesson ID. Each line is either an `injection` or `outcome` record.

## Format

```jsonl
{"kind": "injection", "id": "pol-79e52d7d", "task_id": "T-020", "session_id": "ses_yyy", "timestamp": "2026-03-25T10:00:00Z"}
{"kind": "outcome", "id": "pol-79e52d7d", "task_id": "T-020", "outcome": "success", "evidence": "Theory-sim delta within 1.5%.", "evaluated_at": "2026-03-26T09:00:00Z"}
```

## Outcome values

- `success` — injected; warned failure did not recur
- `failure` — injected; warned failure still recurred
- `unknown` — injection recorded but outcome not yet evaluated

## Written by

- `injection` records: architect at ExecPlan creation time
- `outcome` records: reviewer at task closeout
