# Feature: CLI and Desktop Clients

## Problem

Architects need both terminal and GUI surfaces over the same local API.

## User stories

- As a CLI user, I run `metaagent studio` flows against `http://127.0.0.1:8000`.
- As a Desktop user, the Tauri app calls the same FastAPI core (today: IPC `greet` smoke only; API wiring is next).

## How to use

### Desktop (current)

```bash
cd apps/desktop && pnpm dev          # frontend only
# or
DISPLAY=:1 pnpm tauri dev            # full desktop
```

### API (local core)

```bash
cd apps/api && uvicorn app.main:app --reload --port 8000
```

### Intended wiring

| Client | Transport |
|--------|-----------|
| CLI | HTTP to FastAPI |
| Desktop | HTTP to FastAPI (or Rust proxy) |
| Engine | In-process services behind routers |

## Acceptance

- Docs describe the contract; Desktop UI change is out of scope for this PR
- Health endpoint proves API readiness for clients
