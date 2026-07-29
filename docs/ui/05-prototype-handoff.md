# Prototype Handoff

## Structure

```
apps/desktop/src/
  App.tsx                 # view switch (reads persisted ui state)
  copy/en.ts              # all user-facing strings
  hooks/useAppState.ts    # subscribe to persisted UI state
  hooks/useActivityLog.ts # subscribe to activity log
  lib/storage.ts          # localStorage helpers (mas.* keys)
  lib/appState.ts         # view, idea, wizard, settings — stateful
  lib/logger.ts           # structured activity log (persisted)
  lib/apiClient.ts        # mock | http seam + session/check/kits/connectors
  styles/tokens.css
  components/shell/
  components/ui/
  views/                  # Home, Studio, Check, Improve, Kits, Connections, Settings
```

## State & logging

- UI state (`view`, idea, studio wizard, settings) persists via `appState` → `localStorage` (`mas.ui_state`).
- Domain data (session, check result, kits, connectors, MCP) persists via `apiClient` → `mas.session`, `mas.check`, etc.
- `logger` appends structured entries (`level`, `source`, `message`, optional `data`) to `mas.activity_log` and mirrors to the browser console. View / clear under Settings → Activity log.

## Wiring FastAPI

1. Set `VITE_API_MODE=http` and `VITE_API_BASE=http://127.0.0.1:8000`.
2. Implement methods in `apiClient.ts` that today return mock data — keep the same TypeScript shapes.
3. Map wizard steps to:
   - `POST /api/v1/projects` + `/sessions`
   - discovery start/answer/finalize
   - flows generate/approve
   - allocation + architecture
   - package build / simulate / improve / packs
   - connectors + MCP (`/api/v1/connectors`, `/api/v1/mcp/servers`)

## Extending a screen

1. Add copy keys to `copy/en.ts`.
2. Compose with `GlassPanel` / `VapButton` only (avoid new card systems).
3. Call `apiClient` — never `fetch` from views.

## Non-goals for v1 UI

- Live LangGraph canvas editing
- Multi-user accounts
