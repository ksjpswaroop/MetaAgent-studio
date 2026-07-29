# Product Requirements Document (PRD)
## Project Name: MetaAgent Studio (`MetaAgent-studio`)
**Version**: 1.0.0  
**Author**: Swaroop & MetaAgent Engineering Team  
**Status**: Draft / Spec Approved  
**Target Release**: Q3 2026  

---

## 1. Executive Overview
MetaAgent Studio is an interactive developer tool and meta-agent orchestrator that designs, validates, and scaffolds multi-agent systems. It transforms natural language user intents into formal multi-agent architectures, applies a rigorous 3-Tier Intelligence Allocation Matrix (Code vs Classical ML vs Generative LLMs), and generates production-ready LangGraph/Pydantic codebases.

---

## 2. Problem Statement & Market Background
Building multi-agent systems is currently chaotic. Developers often:
1. Default every step to costly, slow LLM calls (e.g. asking an LLM to parse a date or check an integer condition).
2. Fail to define explicit Pydantic schemas for state transitions, leading to fragile systems.
3. Lack an interactive visual alignment phase where stakeholders verify execution topologies before code generation.
4. Omit deterministic verification gates that prevent agents from performing unsafe external side-effects.

---

## 3. Product Vision & Goals
* **Goal 1**: Reduce token consumption and response latency in generated agent systems by 40-60% through 3-Tier Intelligence Allocation.
* **Goal 2**: Eliminate schema drift by auto-generating typed Pydantic state models and LangGraph state nodes.
* **Goal 3**: Provide a seamless interactive CLI and Desktop (Tauri 2) experience for step-by-step system design.
* **Goal 4**: Guarantee 100% runnable code scaffold exports with SQLite checkpointing and unit test suites.

---

## 4. User Personas & Target Audience
* **Persona A: Senior AI Architect (Enterprise)** — Needs standardized agent topologies, strict data privacy, and deterministic auditing gates.
* **Persona B: Startup Founder / Full-Stack Engineer** — Wants to go from plain-text idea to working multi-agent backend in under 10 minutes.
* **Persona C: Quant / Operations Specialist** — Needs deterministic ML scoring and data rules paired with LLM synthesis.

---

## 5. Scope & Non-Goals
### In Scope
* Interactive multi-turn discovery Q&A.
* Sample execution flow generator (textual + ASCII/Excalidraw diagram output).
* 3-Tier Intelligence Allocator (Tier 1: Code, Tier 2: Classical ML/Stats, Tier 3: Generative LLMs).
* Pydantic state schema generator & LangGraph workflow graph composer.
* Code scaffolding exporter (Python, FastAPI, SQLite, Pytest, Dockerfile, Tauri app config).

### Out of Scope (Non-Goals v1.0)
* Autonomous live deployment to Kubernetes/AWS (scaffold includes Dockerfile/docker-compose, but cloud infra provisioning is out of scope for v1.0).
* Visual drag-and-drop node graph GUI editing (v1.0 uses terminal/Tauri text & structured selection; node graph editor is planned for v2.0).

---

## 6. Detailed Feature Specifications

### Feature 1: Intent Ingestion & Scope Discovery Engine
* **Description**: Takes raw prompt and conducts a 3 to 5-question boundary clarification dialogue.
* **Requirements**:
  * Identify event triggers (webhook vs polling vs manual trigger).
  * Identify external tool dependencies (APIs, databases, web scraping).
  * Identify human-in-the-loop requirements (auto-execute vs human sign-off).
  * Output a structured `ScopeEnvelope` JSON contract.

### Feature 2: Sample Execution Flow & Alignment Gate
* **Description**: Generates 2–3 sample execution scenarios (Happy path, Edge case, Failure/Fallback path).
* **Requirements**:
  * Present human-readable step breakdown with visual ASCII flow chart.
  * Allow user commands: `[Accept]`, `[Modify step N]`, `[Add fallback node]`, `[Re-route]`.
  * Freeze execution topology upon user approval.

### Feature 3: 3-Tier Intelligence Allocation Matrix Engine
* **Description**: Evaluates each step in the approved flow against allocation rules.
* **Requirements**:
  * **Tier 1 (Deterministic Code)**: Assign for math, JSON parsing, regex, schema coercion, SQL queries, auth.
  * **Tier 2 (Deterministic AI / Classical ML)**: Assign for embeddings search, XGBoost risk scoring, Cosine similarity, deduplication.
  * **Tier 3 (Generative LLMs / Agents)**: Assign for unstructured language understanding, multi-step planning, open-ended draft generation.
  * Provide explanation per allocation step.

### Feature 4: Agent & Tool Topology Designer
* **Description**: Generates persona definitions, system prompts, tool whitelists, and model size pinning.
* **Requirements**:
  * Define specialized agents with single-responsibility guidelines.
  * Enforce JSON output mode with markdown fence stripping on all LLM agents.
  * Map explicit tools (REST, Python functions, MCP endpoints) per agent.

### Feature 5: Shared State Architecture & LangGraph Composer
* **Description**: Designs the Pydantic `BaseModel` state structure and constructs the LangGraph `StateGraph`.
* **Requirements**:
  * State variables must have explicit typing and default initializers.
  * Nodes map to Python async functions.
  * Edges define conditional routing based on state fields.
  * Support SQLite checkpointing (`SqliteSaver` / local DB file).

### Feature 6: Deterministic Verification Gate System
* **Description**: Injects validation gates before state changes or external side-effects.
* **Requirements**:
  * Pre-execution gates: validate inputs against schema before calling external APIs.
  * Post-execution gates: check PII sanitization, output length, rate limits, and test runner results.

### Feature 7: Code Scaffolding Exporter
* **Description**: Outputs a complete, runnable directory structure.
* **Requirements**:
  * Generated files: `config.json`, `state.py`, `agents/*.py`, `tools/*.py`, `gates/*.py`, `graph.py`, `main.py`, `test_workflow.py`, `Dockerfile`, `README.md`.
  * Include automated `pytest` test suite covering sample flows.

---

## 7. System Architecture & Workflows
```
User Input
   │
   ▼
[1. RequirementsArchitectAgent] ──► Generates ScopeEnvelope JSON
   │
   ▼
[2. WorkflowDesignerAgent]     ──► Generates Sample Scenarios & ASCII Chart
   │                                   │ (User Acceptance Gate)
   ▼                                   ▼
[3. IntelligenceAllocatorAgent] ──► Assigns Tier 1 / Tier 2 / Tier 3
   │
   ▼
[4. SystemArchitectAgent]      ──► Generates Pydantic State & Agent Topologies
   │
   ▼
[5. CodeScaffoldingAgent]      ──► Writes full project directory & runs pytest
```

---

## 8. Non-Functional Requirements (NFRs)
* **Performance**: Scaffolding complete project output must take < 30 seconds on local LLM or cloud API.
* **Token Efficiency**: MetaAgent Studio internal prompt tokens must stay under 15,000 tokens per system design session.
* **Code Quality**: Generated Python code must satisfy `ruff` linting and `mypy` type checking without errors.
* **Reliability**: 100% of scaffolded projects must pass their generated `pytest` suite upon creation.
* **Security**: No credentials stored in generated code; all secrets loaded via `.env` / environment variables.

---

## 9. Monetization & Go-To-Market
* **Open Source Core (Apache 2.0)**: CLI tool and local LangGraph/SQLite generator.
* **Pro Tier (SaaS / Enterprise)**:
  * Team collaboration on agent topologies.
  * One-click cloud deployment (AWS ECS, Modal, Fly.io).
  * Automated security auditing and compliance reports for generated agents.

---

## 10. Engineering Roadmap & Milestones

| Phase | Duration | Core Deliverables |
| :--- | :--- | :--- |
| **Phase 1: Core Engine** | Weeks 1–3 | CLI discovery engine, ScopeEnvelope schema, WorkflowDesignerAgent, ASCII flow rendering |
| **Phase 2: Allocator & Scaffolder** | Weeks 4–6 | 3-Tier Allocation rules engine, LangGraph Pydantic code generation, SQLite state persistence |
| **Phase 3: Verification & Test Suite** | Weeks 7–9 | Deterministic gate generator, automated pytest code synthesis, ruff/mypy validation |
| **Phase 4: Desktop UI & Tauri App** | Weeks 10–12 | Tauri 2 + React UI wrapper, visual flow review tab, exported project manager |
