# Problem and Solution

## The problem

Building multi-agent systems is chaotic. Teams typically:

1. **Default every step to an LLM** — date parsing, integer checks, regex, and schema coercion burn tokens and add latency.
2. **Ship fragile state** — unstructured dicts between agents cause schema drift and silent failures.
3. **Skip alignment** — stakeholders never verify execution topologies before code generation.
4. **Omit verification gates** — agents perform side-effects (API writes, DB mutations) without pre/post validation.

## The solution

**MetaAgent Studio** is an interactive meta-agent orchestrator that:

1. Clarifies scope via short Q&A → `ScopeEnvelope`
2. Generates sample execution flows and freezes topology only after human approval
3. Assigns every step to **Tier 1 (Code)**, **Tier 2 (Classical ML)**, or **Tier 3 (LLM)**
4. Designs typed Pydantic state, agent personas, and tool contracts
5. Scaffolds a runnable LangGraph project with SQLite checkpointing, gates, and pytest

## 3-Tier Intelligence Allocation Matrix

| Tier | Name | Use when | Examples |
|------|------|----------|----------|
| 1 | Deterministic Code | Zero ambiguity, strict safety | Schema validation, SQL, auth, regex |
| 2 | Classical ML / Stats | Numerical/pattern matching on structured data | Embeddings search, XGBoost scoring, BM25 |
| 3 | Generative LLM / Agent | Unstructured reasoning and synthesis | Email understanding, multi-step planning, drafts |

Routing Tier 1/2 work away from LLMs targets **40–60%** token and latency reduction in generated systems.

## Success metrics

- **Token Efficiency Score** — % of steps offloaded from Tier 3 to Tier 1/2
- **First-Pass Compilation Rate** — % of scaffolds that build and pass initial gates
- **User Flow Acceptance Rate** — % of sample flows approved without major rewrites

## How Studio itself is used

1. Open Desktop or CLI → create a project/session
2. Answer 3–5 discovery questions
3. Review Happy / Ambiguity / Failure scenarios → Accept or modify
4. Review tier allocations (override if needed)
5. Inspect architecture blueprint
6. Run scaffold → open exported project
7. (Optional) Activate a Pro license key for collaboration stubs, deploy stubs, and audit stubs
