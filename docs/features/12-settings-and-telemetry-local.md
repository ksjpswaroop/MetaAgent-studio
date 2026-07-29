# Feature: Settings (Local)

## Problem

Users need persistent local preferences (export path, token budget, timeouts) without accounts.

## User stories

- As a developer, I set default export directory, max tokens per session, and HTTP timeouts.

## User flow

1. `GET /api/v1/settings` → key/value map
2. `PUT /api/v1/settings` with partial updates
3. Optional `telemetry_enabled` flag (default false; local-only, no PII)

## API

| Method | Path |
|--------|------|
| GET | `/api/v1/settings` |
| PUT | `/api/v1/settings` |

## Default keys

| Key | Default |
|-----|---------|
| `export_path` | `~/MetaAgentExports` |
| `token_budget` | `15000` |
| `http_timeout_seconds` | `30` |
| `default_model` | `qwen2.5-coder:7b` |
| `telemetry_enabled` | `false` |

## Tables

`settings`

## Acceptance

- Values stored as JSON in `value_json`
- Invalid types rejected with 422
