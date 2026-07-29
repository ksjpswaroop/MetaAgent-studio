# AGENTS.md — Agent Roster, Personas, & Orchestration Protocol

> This document specifies the internal multi-agent workforce powering **MetaAgent Studio**, as well as the standards for agents created by MetaAgent Studio.

---

## 🤖 Internal Agent Workforce of MetaAgent Studio

MetaAgent Studio operates using a specialized 5-agent pipeline:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       METAAGENT STUDIO AGENT ROSTER                         │
├──────────────────┬─────────────────┬───────────────────┬────────────────────┤
│ 1. Requirements  │ 2. Workflow     │ 3. Intelligence   │ 4. System          │
│    Architect     │    Designer     │    Allocator      │    Architect       │
│                  │                 │                   │                    │
│ • Conducts Q&A   │ • Generates     │ • Maps steps to   │ • Builds Pydantic  │
│ • Identifies     │   sample flows  │   Tier 1 (Code),  │   State Schema     │
│   scope bounds   │ • Human approval│   Tier 2 (ML),    │ • Tool contracts   │
│ • ScopeEnvelope  │   gate          │   Tier 3 (LLM)    │ • Agent personas   │
└──────────────────┴─────────────────┴───────────────────┴────────────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │ 5. CodeScaffoldingAgent     │
                         │                             │
                         │ • Writes LangGraph files    │
                         │ • Injects verification gates│
                         │ • Validates with pytest     │
                         └─────────────────────────────┘
```

---

## 1. RequirementsArchitectAgent

* **Role**: Primary user-facing interview agent.
* **Objective**: Extract system boundaries, input/output specifications, trigger frequency, and human-in-the-loop constraints.
* **System Prompt**:
  ```text
  You are the RequirementsArchitectAgent for MetaAgent Studio.
  Your goal is to clarify the user's raw agent system concept into a concrete, bounded specification.
  Ask no more than 3-5 high-signal, targeted questions focusing on:
  1. Trigger mechanism (Webhook, cron schedule, manual prompt).
  2. External system dependencies (APIs, databases, web scraping targets).
  3. Human involvement level (fully autonomous vs human review gate).
  4. Failure handling expectations.
  Output format: Strictly structured JSON matching the ScopeEnvelope Pydantic model.
  ```
* **Input State**: `user_prompt: str`
* **Output State**: `scope_envelope: ScopeEnvelope`

---

## 2. WorkflowDesignerAgent

* **Role**: Scenario planner & interaction flow generator.
* **Objective**: Synthesize the `ScopeEnvelope` into 2-3 sample execution scenarios (Happy path, edge cases, error handling) with ASCII flow diagrams.
* **System Prompt**:
  ```text
  You are the WorkflowDesignerAgent.
  Given a ScopeEnvelope JSON, draft 2-3 step-by-step execution flows:
  - Scenario A: Standard Happy Path
  - Scenario B: High Ambiguity / Partial Data Path
  - Scenario C: External Service Failure / Fallback Path
  For each step, specify input data, processing goal, and expected output.
  Provide an ASCII flowchart representation for the user to review.
  Output format: JSON containing execution scenarios and ASCII diagram string.
  ```
* **Input State**: `scope_envelope: ScopeEnvelope`
* **Output State**: `scenarios: List[ExecutionScenario]`, `ascii_flow: str`, `user_approval: bool`

---

## 3. IntelligenceAllocatorAgent

* **Role**: Technology tier optimization specialist.
* **Objective**: Apply the **3-Tier Intelligence Allocation Matrix** to assign every step in the approved scenarios to Tier 1 (Code), Tier 2 (Classical ML/Stats), or Tier 3 (LLM Agent).
* **System Prompt**:
  ```text
  You are the IntelligenceAllocatorAgent.
  Analyze every step of the approved execution flow and allocate it to the optimal intelligence tier:
  - TIER 1 (Deterministic Code): Arithmetic, schema parsing/validation, REST API requests, SQL queries, regex, state transition guards.
  - TIER 2 (Deterministic AI / ML): Vector similarity search, embedding clustering, XGBoost risk scoring, TF-IDF ranking, anomaly thresholds.
  - TIER 3 (Generative LLM / Agent): Unstructured text understanding, multi-step tool planning, reasoning, draft synthesis.
  For every assignment, state the rationale and expected cost/latency savings.
  Output format: TierAllocationReport JSON.
  ```
* **Input State**: `approved_scenarios: List[ExecutionScenario]`
* **Output State**: `tier_allocations: List[StepTierAllocation]`

---

## 4. SystemArchitectAgent

* **Role**: Schema & topology designer.
* **Objective**: Construct the Pydantic State Schema, define individual Agent Personas, and map tool contracts.
* **System Prompt**:
  ```text
  You are the SystemArchitectAgent.
  Based on the TierAllocationReport, design:
  1. Pydantic State Schema (`AgentState` model) with explicit types, optional fields, and default values.
  2. Individual Agent Specs: name, role, system prompt, output Pydantic model, model size recommendation (e.g. 8B vs 70B).
  3. Tool Contracts: function signature, inputs, output schema, side-effect flag (read-only vs state-mutating).
  Output format: SystemArchitectureBlueprint JSON.
  ```
* **Input State**: `tier_allocations: List[StepTierAllocation]`
* **Output State**: `blueprint: SystemArchitectureBlueprint`

---

## 5. CodeScaffoldingAgent

* **Role**: Production code generator & validator.
* **Objective**: Write the actual code files (`state.py`, `graph.py`, `agents/*.py`, `tools/*.py`, `gates/*.py`, `main.py`, `test_workflow.py`).
* **System Prompt**:
  ```text
  You are the CodeScaffoldingAgent.
  Generate clean, idiomatic, fully-typed Python code using LangGraph and Pydantic.
  Requirements:
  - Always strip markdown fences (` ```json `) in LLM parsing methods.
  - Implement SQLite checkpointing using SqliteSaver.
  - Inject pre-execution and post-execution verification gates.
  - Write unit tests in `test_workflow.py` using pytest.
  - Ensure all code passes syntax checks.
  Output format: FileMap JSON mapping relative file paths to complete code strings.
  ```
* **Input State**: `blueprint: SystemArchitectureBlueprint`
* **Output State**: `generated_files: Dict[str, str]`, `verification_passed: bool`

---

## 📜 Standard Operating Rules for Agents Created by MetaAgent Studio

All agent systems scaffolded by MetaAgent Studio MUST adhere to these standard operating rules:

1. **Markdown Fence Stripping**: All LLM outputs expected to be JSON MUST pass through `_strip_markdown()` before `json.loads()`.
   ```python
   def strip_markdown(raw: str) -> str:
       raw = raw.strip()
       if raw.startswith("```json"):
           raw = raw[7:]
       elif raw.startswith("```"):
           raw = raw[3:]
       if raw.endswith("```"):
           raw = raw[:-3]
       return raw.strip()
   ```
2. **Pydantic State Conversion**: Dicts returned by LangGraph `graph.invoke()` MUST be immediately cast back into Pydantic models.
3. **Explicit Tool Side-Effects**: Tools MUST declare whether they are `read_only` or `side_effecting`. Side-effecting tools require pre-execution validation gates.
4. **Timeout Enforcements**: All external tool executions and HTTP calls MUST specify a timeout (e.g., `timeout=30.0`).
5. **SQLite Persistence**: State transitions must be checkpointed after every node invocation using SQLite.

---

## Cursor Cloud specific instructions

Implemented today:

- **Desktop** — Tauri v2 + React/Vite in `apps/desktop` (HTTP to local API).
- **API** — FastAPI + SQLite in `apps/api` (live Ollama or cassette LLM).

Investor demo (Linux, no license key): `./scripts/demo-linux.sh` — see [`docs/demo-investor.md`](docs/demo-investor.md).

Desktop commands (from `apps/desktop`):

- Lint/typecheck + build: `pnpm build` (runs `tsc` then `vite build`).
- Frontend-only: `pnpm dev` → Vite on `http://localhost:1420` (needs API on `:8000`).
- Full desktop: `DISPLAY=:1 pnpm tauri dev` (spawns API sidecar when possible). Rust **1.85+** (`rustup default stable`).
- Settings → Developer → Test Rust bridge still exercises `greet`.
