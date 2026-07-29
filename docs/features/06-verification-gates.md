# Feature: Verification Gates

## Problem

Side-effecting tools need pre-execution validation; outputs need post-checks (PII, budget, length).

## User stories

- As an architect, I configure schema/PII/cost gates and dry-run them before scaffold.

## User flow

1. List default gates for session
2. Patch configs (budgets, enable/disable)
3. Dry-run → `gate_runs` rows

## API

| Method | Path |
|--------|------|
| GET | `/api/v1/gates/{session_id}` |
| PATCH | `/api/v1/gates/{session_id}/configs/{gate_id}` |
| POST | `/api/v1/gates/{session_id}/dry-run` |
| GET | `/api/v1/gates/{session_id}/runs` |

## Tables

`gate_configs`, `gate_runs`

## Acceptance

- Side-effecting tools imply at least one pre gate in stub defaults
- Dry-run persists pass/fail details
