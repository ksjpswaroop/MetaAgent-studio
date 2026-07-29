# Feature: LLM Providers

## Problem

Studio must work local-first (Ollama) with cloud fallback without storing API secrets in the DB.

## User stories

- As a developer, I enable Ollama and optionally configure cloud providers via env var names.
- Health checks record latency and failures.

## User flow

1. List providers (seeded on first boot)
2. Patch priority / default model / enabled
3. Test connection → `provider_health_checks`

## API

| Method | Path |
|--------|------|
| GET | `/api/v1/providers` |
| PATCH | `/api/v1/providers/{id}` |
| POST | `/api/v1/providers/{id}/test` |
| PUT | `/api/v1/providers/order` |

## Tables

`llm_providers`, `provider_health_checks`

## Acceptance

- Secrets never stored; only `api_key_env_var` names
- Default seed includes Ollama first in priority
