# MetaAgent Studio UI

Vaporwave glass design system and prototype for non-technical users.

## Open the prototype

```bash
cd apps/desktop
pnpm install
pnpm dev
# http://localhost:1420
```

Mock API mode is default (`VITE_API_MODE=mock`). To point at the local FastAPI core later:

```bash
export VITE_API_MODE=http
export VITE_API_BASE=http://127.0.0.1:8000
pnpm dev
```

## Design docs

| Doc | Purpose |
|-----|---------|
| [01-vision-and-principles.md](01-vision-and-principles.md) | Non-tech + vaporwave glass rules |
| [02-flows-low-fidelity.md](02-flows-low-fidelity.md) | Lo-fi flows, menus, empty/error states |
| [03-high-fidelity-spec.md](03-high-fidelity-spec.md) | Screens, copy, components, tokens |
| [04-mockups.md](04-mockups.md) | Links to static HTML mockups |
| [05-prototype-handoff.md](05-prototype-handoff.md) | Extending UI and wiring FastAPI |

Static mockups (no build): [mockups/](mockups/)

## Tokens (summary)

| Token | Role |
|-------|------|
| Magenta / cyan / peach | Sunset vapor accents |
| Glass fill + border | Frosted panels |
| CRT scanlines | Subtle retro grain overlay |
| Display font | Space Grotesk |
| Body font | Outfit |
