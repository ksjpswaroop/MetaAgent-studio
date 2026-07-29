# High-Fidelity Spec

## Tokens

| Name | Value (approx) | Use |
|------|----------------|-----|
| `--vap-magenta` | `#ff2bd6` | Accents, active nav |
| `--vap-cyan` | `#2de2e6` | Secondary accent, links |
| `--vap-peach` | `#ff9f7a` | Warm highlight |
| `--vap-night` | `#12081f` | Deep base under mesh |
| `--glass-bg` | `rgba(255,255,255,0.08)` | Panel fill |
| `--glass-border` | `rgba(255,255,255,0.22)` | Panel edge |
| `--glass-blur` | `16px` | Backdrop blur |
| Display | Space Grotesk | Titles / brand |
| Body | Outfit | UI copy |

## Shell

- Left rail (~200px): brand mark top, nav items with soft active glass pill
- Main: frosted content well
- Status pill top-right: Ready / Thinking…
- CRT overlay pseudo-element on `body::after`, pointer-events none

## Screens

### Home

- Full-bleed sunset mesh; brand wordmark large
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

### Settings

- License key, Local/Cloud brain, export folder
- Collapsed “Developer” with Tauri greet test

## Component inventory

`AppShell`, `GlassPanel`, `VapButton`, `VapInput`, `VapTextarea`, `StepDots`, `PlainChatBubble`, `ScoreRing`, `KitTile`, `NavItem`
