# Prototype Handoff

## Structure

```
apps/desktop/src/
  App.tsx                 # view state switch
  copy/en.ts              # all user-facing strings
  lib/apiClient.ts        # mock | http seam
  styles/tokens.css
  components/shell/
  components/ui/
  views/                  # Home, Studio, Check, Improve, Kits, Settings
```

## Wiring FastAPI

1. Set `VITE_API_MODE=http` and `VITE_API_BASE=http://127.0.0.1:8000`.
2. Implement methods in `apiClient.ts` that today return mock data — keep the same TypeScript shapes.
3. Map wizard steps to:
   - `POST /api/v1/projects` + `/sessions`
   - discovery start/answer/finalize
   - flows generate/approve
   - allocation + architecture
   - package build / simulate / improve / packs

## Extending a screen

1. Add copy keys to `copy/en.ts`.
2. Compose with `GlassPanel` / `VapButton` only (avoid new card systems).
3. Call `apiClient` — never `fetch` from views.

## Non-goals for v1 UI

- Live LangGraph canvas editing
- Multi-user accounts
