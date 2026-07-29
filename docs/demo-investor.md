# Investor demo — MetaAgent Studio (Tauri + live Ollama)

## What you will see

A desktop app that turns a plain-language idea into a packaged agent kit:

1. **Start** — describe the helper  
2. **Build my agent** — answer questions, approve the plan, see who does what, build  
3. **Make sure it works** — real package + simulation score  
4. **Make it better** — edge cases, coding prompts, iterate  
5. **My saved kits** — publish and reuse packs  
6. **Connections** — Hermes Agent + apps + MCP servers  
7. **Settings** — brain (Ollama) test, activity log — **no license key**

## One-command launch (Linux)

```bash
# Terminal A (if not already running)
ollama serve
ollama pull qwen2.5-coder:1.5b

# Terminal B
./scripts/demo-linux.sh
```

Requirements: Python 3.11+, pnpm, Rust 1.85+, Ollama, `DISPLAY` for the GUI (`:1` on the Cloud VM).

Env set by the script:

| Variable | Value |
|----------|--------|
| `METAAGENT_LLM_MODE` | `live` |
| `METAAGENT_DEMO_UNLOCK` | `1` |
| `METAAGENT_DB_PATH` | `~/.metaagent/studio-demo.db` |
| `VITE_API_MODE` | `http` |

## Unsigned Linux build

```bash
cd apps/desktop
pnpm install
pnpm tauri build
# Artifacts under src-tauri/target/release/bundle/{appimage,deb}
```

macOS signing/notarization is intentionally out of scope for this demo.

## If the brain is offline

Status pill shows **Brain offline**. Start Ollama, then Settings → **Test brain (Ollama)**.
