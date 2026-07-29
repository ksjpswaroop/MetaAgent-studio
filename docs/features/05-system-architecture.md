# Feature: System Architecture Blueprint

## Problem

Agent personas, tools, and shared state must be explicit before codegen.

## User stories

- As an architect, I get a Pydantic `AgentState` sketch, agent specs, and tool contracts with side-effect flags.

## User flow

1. Build blueprint from allocations
2. Inspect agents, tools, graph topology JSON
3. Proceed to gates / scaffold

## API

| Method | Path |
|--------|------|
| POST | `/api/v1/architecture/{session_id}/build` |
| GET | `/api/v1/architecture/{session_id}` |
| GET | `/api/v1/architecture/{session_id}/agents` |
| GET | `/api/v1/architecture/{session_id}/tools` |
| GET | `/api/v1/architecture/{session_id}/state-schema` |

## Tables

`architecture_blueprints`, `agent_specs`, `tool_specs`

## Acceptance

- Tools declare `read_only` or `side_effecting`
- Default tool timeout is 30 seconds
