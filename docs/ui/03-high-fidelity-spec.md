# High-Fidelity Spec

## Tokens

| Name | Value (approx) | Use |
|------|----------------|-----|
| `--li-blue` | `#0A66C2` | Primary CTA, active nav, brand |
| `--li-blue-soft` | `#378FE9` | Secondary CTA / accents |
| `--li-blue-dark` | `#004182` | Hover / emphasis |
| `--li-success` | `#057642` | Pass states |
| `--li-surface` | `#EEF3F8` | App background |
| `--li-ink` | `#191919` | Body text |
| `--glass-bg` | `rgba(255,255,255,0.72)` | Panel fill |
| `--glass-border` | `rgba(10,102,194,0.16)` | Panel edge |
| `--glass-blur` | `14px` | Backdrop blur |
| Display | Space Grotesk | Titles / brand |
| Body | Outfit | UI copy |

## Shell

- Left rail (~200px): blue brand mark, white glass nav; active item solid LinkedIn blue
- Main: frosted white content well on cool blue-gray mesh
- Status pill top-right: Ready / Thinking…

## Screens

### Home

- Full-bleed cool blue mesh; brand wordmark large in blue gradient
- One headline: “Turn an idea into a working helper”
- One supporting line
- Large idea textarea + primary CTA “Start building”
- Three example chips (support mail, invoices, research)
- No stats, no secondary cards in first viewport

### Studio wizard

Step dots + title. Steps:

1. Idea (editable)
2. Questions (chat bubbles)
3. Plan approve (three path tabs)
4. Who does what (role rows: Rules / Smart match / AI writer)
5. Build kit (progress + Continue to Check)

### Check

- Score ring (overall)
- Checklist: package written, tests ran, zip ready
- CTA: Make it better / Save kit

### Improve

- Edge case list (plain titles)
- Prompt cards “Ask Cursor to fix” with copy button

### Kits

- Glass tiles: name, score, Fork / Open

### Connections

- Tabs: **Apps & tools** | **MCP servers**
- Apps: Hermes Agent, Gmail, Slack, Notion, Sheets, Webhook; connect / disconnect / test; add custom REST base URL
- MCP: list with transport (local command / SSE / HTTP), turn on/off, test, remove; add form
- Plain status copy (“Looks good” / “Couldn’t reach it”)

### Settings

- License key, Local/Cloud brain, export folder (persisted)
- Activity log (recent actions, clearable, survives refresh)
- Collapsed “Developer” with Tauri greet test

## Component inventory

`AppShell`, `GlassPanel`, `VapButton`, `VapInput`, `VapTextarea`, `StepDots`, `PlainChatBubble`, `ScoreRing`, `KitTile`, `NavItem`
