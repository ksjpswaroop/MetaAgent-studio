# MetaAgent Studio API

Local-first FastAPI core for the MetaAgent Studio desktop/CLI app.

- Single-user (no auth)
- SQLite persistence (`METAAGENT_DB_PATH`, default `~/.metaagent/studio.db`)
- License key unlocks Pro stub routers
- LLM pipeline stages return canned stubs but persist results

## Setup

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export METAAGENT_DB_PATH=/tmp/metaagent-studio-dev.db
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## License stub

Activate Pro with a key matching `MAS-PRO-XXXX-XXXX-XXXX`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/license/activate \
  -H 'content-type: application/json' \
  -d '{"license_key":"MAS-PRO-TEST-KEY1-ABCD"}'
```

## Tests

```bash
cd apps/api
export METAAGENT_DB_PATH=/tmp/metaagent-studio-test.db
pytest -q
```

## Docs

See [`docs/`](../../docs/README.md) for features, user flows, database design, and OpenAPI YAML.
