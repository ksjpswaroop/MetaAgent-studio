# Feature: Flow Alignment Gate

## Problem

Code must not be generated until humans agree on execution topology.

## User stories

- As an architect, I review Happy / Ambiguity / Failure scenarios with ASCII/Mermaid diagrams.
- I Accept, Modify step N, Add fallback, or Re-route before freezing.

## User flow

1. Generate scenarios after scope is ready
2. Inspect ASCII + Mermaid
3. Optionally modify; then Approve → `flow_approved=true`, stage `flow_approved`

## API

| Method | Path |
|--------|------|
| POST | `/api/v1/flows/{session_id}/generate` |
| GET | `/api/v1/flows/{session_id}` |
| POST | `/api/v1/flows/{session_id}/modify` |
| POST | `/api/v1/flows/{session_id}/add-fallback` |
| POST | `/api/v1/flows/{session_id}/re-route` |
| POST | `/api/v1/flows/{session_id}/approve` |

## Tables

`execution_scenarios`, `scenario_steps`, `flow_revision_log`

## Acceptance

- Allocation endpoints return `409` until flow approved
- Revision log records each edit
