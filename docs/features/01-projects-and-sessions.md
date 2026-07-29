# Feature: Projects and Sessions

## Problem

Architects need durable project history and resumable design sessions without a cloud account.

## User stories

- As a developer, I create a named project and start a design session from a natural-language prompt.
- As a developer, I resume a prior session at the last pipeline stage.

## User flow

1. Create project (`POST /api/v1/projects`)
2. Create session with `raw_user_prompt` (`POST /api/v1/sessions`)
3. List/get/update/archive projects as needed
4. Stream or poll `session_events` for progress

## API

| Method | Path | Notes |
|--------|------|-------|
| GET/POST | `/api/v1/projects` | List / create |
| GET/PATCH/DELETE | `/api/v1/projects/{id}` | Get / update / archive |
| GET/POST | `/api/v1/sessions` | List / create |
| GET/PATCH | `/api/v1/sessions/{id}` | Get / patch state |
| GET | `/api/v1/sessions/{id}/events` | Event history |

## Tables

`projects`, `studio_sessions`, `session_events`

## Acceptance

- Project CRUD persists in SQLite and reloads after restart
- Session `stage` advances only through valid transitions
- Deleting/archiving a project cascades session children
