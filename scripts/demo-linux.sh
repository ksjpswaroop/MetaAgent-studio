#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$ROOT/apps/api"
DESKTOP_DIR="$ROOT/apps/desktop"
export DISPLAY="${DISPLAY:-:1}"
export METAAGENT_API_DIR="$API_DIR"
export METAAGENT_LLM_MODE=live
export METAAGENT_DEMO_UNLOCK=1
export METAAGENT_DB_PATH="${METAAGENT_DB_PATH:-$HOME/.metaagent/studio-demo.db}"
export VITE_API_MODE=http
export VITE_API_BASE=http://127.0.0.1:8000

echo "==> MetaAgent Studio investor demo"
echo "    API: $API_DIR"
echo "    Desktop: $DESKTOP_DIR"

if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "ERROR: Ollama is not reachable at http://127.0.0.1:11434"
  echo "Start it with: ollama serve"
  echo "Then pull a model: ollama pull qwen2.5-coder:7b"
  exit 1
fi

MODEL="${METAAGENT_OLLAMA_MODEL:-qwen2.5-coder:1.5b}"
if ! curl -sf http://127.0.0.1:11434/api/tags | grep -q "${MODEL%%:*}"; then
  echo "==> Pulling Ollama model $MODEL (first run may take a while)"
  ollama pull "$MODEL" || true
fi

mkdir -p "$(dirname "$METAAGENT_DB_PATH")"

if [[ ! -d "$API_DIR/.venv" ]]; then
  echo "==> Creating API venv"
  python3 -m venv "$API_DIR/.venv"
  # shellcheck disable=SC1091
  source "$API_DIR/.venv/bin/activate"
  pip install -e "$API_DIR/[dev]"
else
  # shellcheck disable=SC1091
  source "$API_DIR/.venv/bin/activate"
fi

# Prefer a clean API with investor demo env (avoid stale cassette processes)
if curl -sf http://127.0.0.1:8000/health >/dev/null; then
  MODE=$(curl -s http://127.0.0.1:8000/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('llm_mode',''))" 2>/dev/null || true)
  DEMO=$(curl -s http://127.0.0.1:8000/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('demo_unlock',False))" 2>/dev/null || true)
  if [[ "$MODE" != "live" || "$DEMO" != "True" ]]; then
    echo "==> Stopping stale API on :8000 (want live + demo_unlock)"
    pkill -f 'uvicorn app.main:app' 2>/dev/null || true
    sleep 1
  fi
fi

if ! curl -sf http://127.0.0.1:8000/health >/dev/null; then
  echo "==> Starting FastAPI on :8000 (live + demo unlock)"
  (
    cd "$API_DIR"
    METAAGENT_LLM_MODE=live METAAGENT_DEMO_UNLOCK=1 METAAGENT_DB_PATH="$METAAGENT_DB_PATH" \
      METAAGENT_HTTP_TIMEOUT_SECONDS=120 \
      uvicorn app.main:app --host 127.0.0.1 --port 8000
  ) &
  API_PID=$!
  trap 'kill $API_PID 2>/dev/null || true' EXIT
  for i in $(seq 1 60); do
    if curl -sf http://127.0.0.1:8000/health >/dev/null; then
      break
    fi
    sleep 0.5
  done
  curl -sf http://127.0.0.1:8000/health >/dev/null || {
    echo "ERROR: API failed to start"
    exit 1
  }
else
  echo "==> API already running on :8000 with correct demo env"
fi

echo "==> Health:"
curl -s http://127.0.0.1:8000/health
echo

cd "$DESKTOP_DIR"
if [[ ! -d node_modules ]]; then
  pnpm install
fi

# Prefer Tauri when Rust is available
if command -v cargo >/dev/null && [[ -x "$DESKTOP_DIR/node_modules/.bin/tauri" ]]; then
  echo "==> Launching Tauri (DISPLAY=$DISPLAY)"
  rustup default stable >/dev/null 2>&1 || true
  pnpm tauri dev
else
  echo "==> Tauri/cargo unavailable — launching Vite UI only"
  pnpm dev
fi
