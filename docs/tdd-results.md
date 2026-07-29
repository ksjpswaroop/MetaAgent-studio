# TDD Results — MetaAgent Studio API

## Modes

| Mode | Env | Behavior |
|------|-----|----------|
| Cassette (CI default) | `METAAGENT_LLM_MODE=cassette` | Deterministic offline JSON via `tests/fixtures/llm` + synthetic fallbacks |
| Live | `METAAGENT_LLM_MODE=live` | Real provider HTTP (Ollama → cloud by priority) |

```bash
cd apps/api
source .venv/bin/activate
export METAAGENT_LLM_MODE=cassette
pytest -q
```

Optional live:

```bash
export METAAGENT_LLM_MODE=live
pytest -q -m live_llm   # when markers are added / Ollama running
```

## Suite matrix (cassette)

| Suite | Focus | Status |
|-------|-------|--------|
| `test_health` | DB readiness | pass |
| `test_db_schema` / `test_new_tables` | Core + migration 002 tables | pass |
| `test_license` | Pro gate 402/200 | pass |
| `test_projects_crud` | Project/session CRUD | pass |
| `test_router_stubs` | Happy path smoke | pass |
| `test_strip_markdown` | JSON fence stripping SOP | pass |
| `test_full_pipeline` | Design→package, edge/sim/prompts/improve/packs | pass |

**Latest cassette run:** 13 passed.

## Sample projects

Defined in `apps/api/tests/fixtures/sample_projects.json`:

1. Support Triage  
2. Invoice Ingest  
3. Research Summarizer  

Pipeline exercised: discovery → scope → flows → approve → allocation → architecture → gates → package (tree + zip + checksums + pytest sandbox) → edge cases → simulate → coding-gap prompts → improve iterate → publish pack → fork.

## Known limitations

- Cloud deploy (`/api/v1/deploy`) remains a licensed Pro stub (local package only).
- Live LLM quality depends on local Ollama/cloud keys; cassette mode does not call the network.
- Simulation runner uses deterministic in-process evaluation of scenarios/edge fixtures (not full LangGraph runtime execution of generated code).
- Desktop UI not wired to new endpoints yet.

## Philosophy loop coverage

idea → design (LLM engines) → TDD/tests (generated package pytest) → develop (scaffold FileMap) → test (sandbox) → package (zip/checksums) → distribute locally (export path) → simulate → edge cases → coding-gap prompts → hill-climb → agent packs reuse.
