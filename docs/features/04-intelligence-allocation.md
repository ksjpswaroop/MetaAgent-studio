# Feature: 3-Tier Intelligence Allocation

## Problem

Teams over-assign LLMs to deterministic work, inflating cost and failure rates.

## User stories

- As an architect, I see each step assigned Tier 1/2/3 with rationale and can override.

## User flow

1. After flow approval, run allocator
2. Review table of step → tier → tech
3. Optionally override a step's tier
4. Recompute if needed

## API

| Method | Path |
|--------|------|
| POST | `/api/v1/allocation/{session_id}/run` |
| GET | `/api/v1/allocation/{session_id}` |
| PATCH | `/api/v1/allocation/{session_id}/steps/{step_id}` |
| POST | `/api/v1/allocation/{session_id}/recompute` |

## Tables

`step_allocations`

## Acceptance

- Requires `flow_approved`
- Overrides set `user_override=true`
- Suggested tech strings are non-empty in stub data
