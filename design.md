# MetaAgent Studio Architecture & System Design (`design.md`)

> Technical Specification, Data Flow Models, Database Schemas, & UI/UX Architecture

---

## 🏗️ 1. Overall System Architecture

MetaAgent Studio is implemented as a modular Python framework with a CLI interface and optional Desktop (Tauri 2 + React) GUI.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE LAYER                               │
│        ┌──────────────────────────┐      ┌──────────────────────────┐        │
│        │   Rich CLI (Terminal)    │      │  Tauri 2 / React Desktop │        │
│        └────────────┬─────────────┘      └────────────┬─────────────┘        │
└─────────────────────┼─────────────────────────────────┼─────────────────────┘
                      │                                 │
┌─────────────────────▼─────────────────────────────────▼─────────────────────┐
│                          CORE META-AGENT ENGINE                             │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────┐  │
│  │ RequirementsArchitect  │  │   WorkflowDesigner     │  │ Intelligence   │  │
│  │ (ScopeEnvelope Engine) │  │ (Sample Flow Visual)   │  │ Allocator      │  │
│  └───────────┬────────────┘  └───────────┬────────────┘  └───────┬────────┘  │
│              │                           │                       │           │
│  ┌───────────▼────────────┐  ┌───────────▼────────────┐          │           │
│  │   SystemArchitect      │  │    CodeScaffolder      │◄─────────┘           │
│  │ (LangGraph/Pydantic)   │  │   (File Generation)    │                      │
│  └────────────────────────┘  └────────────────────────┘                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                        DATA & STATE PERSISTENCE LAYER                       │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────┐  │
│  │  SQLite Local Database │  │ Pydantic State Models  │  │ Template Engine│  │
│  │ (~/.metaagent/studio.db)│ │ (Type Validation)      │  │ (Jinja2 / AST) │  │
│  └────────────────────────┘  └────────────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 💧 2. Detailed Data Flow & State Lifecycle

The system operates over a strongly typed Pydantic `StudioSessionState`:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class TierType(str, Enum):
    TIER_1_CODE = "TIER_1_CODE"
    TIER_2_CLASSICAL_ML = "TIER_2_CLASSICAL_ML"
    TIER_3_LLM_AGENT = "TIER_3_LLM_AGENT"

class ScopeEnvelope(BaseModel):
    project_name: str
    primary_goal: str
    trigger_type: str  # webhook, cron, manual
    external_tools: List[str]
    human_in_loop: bool
    fallback_strategy: str

class StepAllocation(BaseModel):
    step_id: int
    step_name: str
    description: str
    allocated_tier: TierType
    rationale: str
    suggested_tech: str  # e.g., "Pydantic + Regex", "Sentence-Transformers", "qwen2.5-coder"

class AgentSpec(BaseModel):
    name: str
    role: str
    system_prompt: str
    tools: List[str]
    model_recommendation: str

class ToolSpec(BaseModel):
    name: str
    description: str
    is_side_effecting: bool
    parameters: Dict[str, Any]

class StudioSessionState(BaseModel):
    session_id: str
    raw_user_prompt: str
    scope_envelope: Optional[ScopeEnvelope] = None
    sample_flows: List[Dict[str, Any]] = Field(default_factory=list)
    flow_approved: bool = False
    allocations: List[StepAllocation] = Field(default_factory=list)
    agent_specs: List[AgentSpec] = Field(default_factory=list)
    tool_specs: List[ToolSpec] = Field(default_factory=list)
    generated_files: Dict[str, str] = Field(default_factory=dict)
```

---

## 💾 3. Database Schema (`~/.metaagent/studio.db`)

MetaAgent Studio uses SQLite for session management, project history, license state, and template caching.

> **Canonical schema:** See [`docs/database.md`](docs/database.md) and [`apps/api/app/db/schema.sql`](apps/api/app/db/schema.sql). The sketch below is historical; the running API applies the full migration set (projects, sessions, discovery, flows, allocations, blueprints, gates, scaffold jobs, artifacts, providers, settings, license).

```sql
-- See apps/api/app/db/schema.sql for the full DDL.
-- Core entities include: app_meta, license_state, settings, projects,
-- studio_sessions, scope_envelopes, execution_scenarios, step_allocations,
-- architecture_blueprints, gate_configs, scaffold_jobs, artifacts, llm_providers.
```

---

## 🔒 4. Verification Gate Architecture

Deterministic verification gates sit between agent outputs and system execution nodes:

```python
class VerificationGate:
    """Base class for all pre-execution and post-execution gates."""
    
    @staticmethod
    def validate_schema(data: dict, schema_cls: type) -> bool:
        """Tier 1: Enforces that dict matches Pydantic model exactly."""
        try:
            schema_cls(**data)
            return True
        except Exception as e:
            raise ValueError(f"Verification Gate Failed (Schema Mismatch): {e}")

    @staticmethod
    def sanitize_pii(text: str) -> str:
        """Tier 1: Redacts emails, phone numbers, and keys before LLM call."""
        # Regex sanitization rules...
        return text

    @staticmethod
    def check_cost_budget(tokens_used: int, max_budget: int) -> bool:
        """Tier 1: Ensures run does not exceed token allocation."""
        if tokens_used > max_budget:
            raise MemoryError("Token budget exceeded limit!")
        return True
```

---

## 🖥️ 5. User Interface & Experience Design

### CLI Interface (`metaagent studio`)
Powered by `rich` and `typer`:
* Interactive prompts with color-coded syntax.
* Live rendering of sample flows using ASCII trees.
* Table summary of 3-Tier allocations:
  ```text
  ┌──────┬────────────────────────────┬──────────────────┬───────────────────────────┐
  │ Step │ Step Name                  │ Tier Allocation  │ Tech Stack                │
  ├──────┼────────────────────────────┼──────────────────┼───────────────────────────┤
  │ 1    │ Validate Payload & Auth    │ Tier 1 (Code)    │ Pydantic + FastAPI        │
  │ 2    │ Search Knowledge Base      │ Tier 2 (ML)      │ Cosine + Embeddings       │
  │ 3    │ Reason & Draft Reply       │ Tier 3 (LLM)     │ LangGraph + Local LLM     │
  └──────┴────────────────────────────┴──────────────────┴───────────────────────────┘
  ```

### Desktop UI (Tauri 2 + React)
* **Left Panel**: Interactive Chat & Scope Q&A.
* **Center Panel**: Visual Node Graph Preview & ASCII/Mermaid Renderer.
* **Right Panel**: Real-time Generated Code Inspector & Tier Allocator Configurator.

---

## ⚡ 6. Performance & Local-First Execution Strategy

* **Local LLM Support**: Native compatibility with Ollama (`qwen2.5-coder:7b` / `llama3.1:8b`).
* **Fallback Chain**: Local Ollama → Anthropic / OpenAI / DeepSeek cloud fallback if local model fails.
* **Fast Templating**: File scaffolding uses Jinja2 template rendering + AST syntax verification before disk writes.
