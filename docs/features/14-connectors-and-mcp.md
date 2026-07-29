# Feature: Connectors & MCP

## Problem

Helpers need external apps (email, chat, sheets) and optional MCP tool servers. Users should manage these locally without speaking API jargon.

## User stories

- As a builder, I connect Gmail / Slack / Notion / Sheets / a webhook so my kit can use them.
- As an advanced user, I add MCP servers (stdio, SSE, or HTTP) and turn them on/off.
- As a cautious user, I can test a connection before relying on it.

## User flow

1. Open **Connections** in the desktop app.
2. **Apps & tools** — connect / disconnect / test; optionally add a custom REST base URL.
3. **MCP servers** — add server (command or URL), enable, test, remove.
4. Studio scaffolding (future) reads connected tools when packaging agents.

## API (planned)

| Method | Path |
|--------|------|
| GET | `/api/v1/connectors` |
| POST | `/api/v1/connectors` |
| PATCH | `/api/v1/connectors/{id}` |
| POST | `/api/v1/connectors/{id}/test` |
| GET | `/api/v1/mcp/servers` |
| POST | `/api/v1/mcp/servers` |
| PATCH | `/api/v1/mcp/servers/{id}` |
| DELETE | `/api/v1/mcp/servers/{id}` |
| POST | `/api/v1/mcp/servers/{id}/test` |

## Tables (planned)

`connectors`, `mcp_servers` — secrets never stored; only env var names or OS keychain references.

## Desktop prototype

Mock + localStorage via `apps/desktop/src/lib/apiClient.ts` (`listConnectors`, `listMcpServers`, …). Flip `VITE_API_MODE=http` when the FastAPI routers land.

## Acceptance

- Non-tech labels in UI; MCP behind a clear “advanced” blurb
- Connect / disconnect and enable / disable persist locally in mock mode
- Test actions return a plain success/fail message
- HTTP methods live only in `apiClient`
