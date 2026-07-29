# MetaAgent Studio Documentation

Interactive meta-agent platform for designing, allocating intelligence tiers, and scaffolding multi-agent systems.

## How to read these docs

1. Start with [PROBLEM_AND_SOLUTION.md](PROBLEM_AND_SOLUTION.md) for product context.
2. Read [user-flows.md](user-flows.md) for end-to-end journeys.
3. Use [database.md](database.md) for the SQLite schema (system of record).
4. Browse [features/](features/) for per-domain specs (flows, tables, API touchpoints).
5. Use [api/openapi.yaml](api/openapi.yaml) as the HTTP contract.
6. Run the stub API in [`apps/api`](../apps/api/README.md).

## Product constraints

- Single-user **desktop** app (local-first)
- **No authentication** (trusted local client)
- **License key** unlocks Pro features (`/api/v1/license`)
- SQLite at `~/.metaagent/studio.db` (override with `METAAGENT_DB_PATH`)
- FastAPI local core API consumed by CLI and Desktop

## Quick start (API stubs)

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export METAAGENT_DB_PATH=/tmp/metaagent-studio-dev.db
uvicorn app.main:app --reload --port 8000
```

- OpenAPI UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Document map

| Document | Purpose |
|----------|---------|
| [PROBLEM_AND_SOLUTION.md](PROBLEM_AND_SOLUTION.md) | Problem, value prop, 3-tier matrix |
| [user-flows.md](user-flows.md) | End-to-end user journeys |
| [database.md](database.md) | SQLite ER design and table dictionary |
| [features/](features/) | Feature-level specs |
| [api/openapi.yaml](api/openapi.yaml) | OpenAPI 3.1 root |
| [../PRD.md](../PRD.md) | Product requirements |
| [../design.md](../design.md) | Architecture (schema superseded by database.md) |
| [../AGENTS.md](../AGENTS.md) | Agent roster and SOPs |

## Feature index

1. [Projects & sessions](features/01-projects-and-sessions.md)
2. [Scope discovery](features/02-scope-discovery.md)
3. [Flow alignment](features/03-flow-alignment.md)
4. [Intelligence allocation](features/04-intelligence-allocation.md)
5. [System architecture](features/05-system-architecture.md)
6. [Verification gates](features/06-verification-gates.md)
7. [Code scaffolding](features/07-code-scaffolding.md)
8. [LLM providers](features/08-llm-providers.md)
9. [Artifacts & export](features/09-artifacts-and-export.md)
10. [CLI & desktop](features/10-cli-and-desktop.md)
11. [License & Pro](features/11-license-and-pro.md)
12. [Settings](features/12-settings-and-telemetry-local.md)
