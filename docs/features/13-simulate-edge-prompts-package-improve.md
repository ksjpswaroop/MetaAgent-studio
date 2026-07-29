# Feature: Simulate, Edge Cases, Prompts, Package, Improve

## Problem

Users need to verify agents before shipping, generate stress cases, fill coding gaps with Cursor/Claude/Codex prompts, package locally, and continuously improve.

## Endpoints

### Edge cases `/api/v1/edge-cases`
- `POST /{session_id}/generate`
- `GET /{session_id}`
- `POST /{session_id}/{case_id}/attach-to-flows`

### Simulate `/api/v1/simulate`
- `POST /{session_id}/run`
- `GET /{session_id}/runs`
- `GET /runs/{run_id}`

### Prompts `/api/v1/prompts`
- `POST /{session_id}/generate` (`tool_target`: cursor|claude|codex|generic)
- `GET /{session_id}`

### Package `/api/v1/package`
- `POST /{session_id}/build` — tree + zip + checksums + optional pytest sandbox
- `POST /{session_id}/verify`
- `GET /{session_id}/packages`

### Improve `/api/v1/improve` + packs
- `POST /{session_id}/iterate`
- `GET /{session_id}/history`
- `POST /{session_id}/publish-local`
- `GET /api/v1/packs`
- `POST /api/v1/packs/{id}/fork`

## Tables

`edge_cases`, `simulation_runs`, `simulation_step_traces`, `coding_gap_prompts`, `packages`, `package_files`, `improvement_iterations`, `agent_packs`
