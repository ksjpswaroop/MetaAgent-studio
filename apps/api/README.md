# MetaAgent Studio API

Local-first FastAPI core for MetaAgent Studio.

- Single-user (no auth); license key unlocks Pro stubs
- SQLite persistence (`METAAGENT_DB_PATH`)
- **LLM-backed** discovery / flows / allocation / architecture (`METAAGENT_LLM_MODE=cassette|live`)
- Simulation, edge cases, coding-gap prompts, local packaging, hill-climb improve + agent packs

## Setup

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export METAAGENT_DB_PATH=/tmp/metaagent-studio-dev.db
export METAAGENT_LLM_MODE=cassette   # or live with Ollama running
uvicorn app.main:app --reload --port 8000
```

- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## License stub

```bash
curl -X POST http://127.0.0.1:8000/api/v1/license/activate \
  -H 'content-type: application/json' \
  -d '{"license_key":"MAS-PRO-TEST-KEY1-ABCD"}'
```

## Tests

```bash
export METAAGENT_LLM_MODE=cassette
pytest -q
```

See [`docs/tdd-results.md`](../../docs/tdd-results.md).

## Loop

idea → LLM design → package (tree/zip/checksums/pytest) → simulate → edge cases → coding-gap prompts → improve → publish pack → fork/reuse
