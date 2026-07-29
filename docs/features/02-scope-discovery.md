# Feature: Scope Discovery

## Problem

Raw prompts are underspecified; systems need triggers, tools, HITL, and failure strategy before design.

## User stories

- As an architect, I answer 3–5 targeted questions and receive a structured `ScopeEnvelope`.

## User flow

1. Start discovery for a session
2. Answer questions (trigger, external tools, HITL, failure handling)
3. Finalize → `ScopeEnvelope` persisted

## API

| Method | Path |
|--------|------|
| POST | `/api/v1/discovery/{session_id}/start` |
| POST | `/api/v1/discovery/{session_id}/answer` |
| GET | `/api/v1/discovery/{session_id}/messages` |
| POST | `/api/v1/discovery/{session_id}/finalize` |
| GET | `/api/v1/discovery/{session_id}/scope` |

## Tables

`discovery_messages`, `scope_envelopes`, `studio_sessions.state_json`

## Acceptance

- At most 3–5 high-signal questions in the stub script
- Finalize rejects incomplete required fields
- Scope stored both normalized and in session snapshot
