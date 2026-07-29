from __future__ import annotations

from app.models.schemas import TierType


DISCOVERY_QUESTIONS = [
    {
        "question_key": "trigger_type",
        "content": "How is this system triggered? (webhook / cron / manual)",
    },
    {
        "question_key": "external_tools",
        "content": "Which external systems are required? (APIs, databases, scraping targets)",
    },
    {
        "question_key": "human_in_loop",
        "content": "Should a human review outputs before side-effects? (yes/no)",
    },
    {
        "question_key": "fallback_strategy",
        "content": "What should happen when an external service fails?",
    },
]


def stub_scenarios(project_name: str) -> list[dict]:
    ascii_flow = (
        f"[{project_name}]\n"
        "  -> Validate Input (T1)\n"
        "  -> Retrieve Context (T2)\n"
        "  -> Reason & Draft (T3)\n"
        "  -> Gate & Emit (T1)"
    )
    mermaid = (
        "flowchart LR\n"
        "  A[Validate] --> B[Retrieve]\n"
        "  B --> C[Reason]\n"
        "  C --> D[Emit]"
    )
    steps = [
        {
            "step_index": 1,
            "name": "Validate Payload & Auth",
            "input_data": {"payload": "webhook_body"},
            "processing_goal": "Schema + signature validation",
            "expected_output": "Validated event object",
        },
        {
            "step_index": 2,
            "name": "Search Knowledge Base",
            "input_data": {"query": "event summary"},
            "processing_goal": "Retrieve top-k context",
            "expected_output": "Ranked snippets",
        },
        {
            "step_index": 3,
            "name": "Reason & Draft Reply",
            "input_data": {"context": "snippets"},
            "processing_goal": "Synthesize response",
            "expected_output": "Draft text",
        },
        {
            "step_index": 4,
            "name": "Post-execution Gates & Emit",
            "input_data": {"draft": "text"},
            "processing_goal": "PII/budget checks then emit",
            "expected_output": "Safe outbound message",
        },
    ]
    return [
        {
            "kind": "happy",
            "title": "Scenario A: Happy Path",
            "ascii_flow": ascii_flow,
            "mermaid_flow": mermaid,
            "sort_order": 0,
            "steps": steps,
        },
        {
            "kind": "ambiguity",
            "title": "Scenario B: High Ambiguity / Partial Data",
            "ascii_flow": ascii_flow + "\n  -> Clarify Missing Fields",
            "mermaid_flow": mermaid + "\n  B --> E[Clarify]",
            "sort_order": 1,
            "steps": steps
            + [
                {
                    "step_index": 5,
                    "name": "Clarify Missing Fields",
                    "input_data": {"missing": ["customer_id"]},
                    "processing_goal": "Request clarification",
                    "expected_output": "Follow-up question",
                }
            ],
        },
        {
            "kind": "failure",
            "title": "Scenario C: External Service Failure",
            "ascii_flow": ascii_flow + "\n  -> Fallback Cache / Queue",
            "mermaid_flow": mermaid + "\n  B --> F[Fallback]",
            "sort_order": 2,
            "steps": steps
            + [
                {
                    "step_index": 5,
                    "name": "Fallback Cache / Queue",
                    "input_data": {"error": "timeout"},
                    "processing_goal": "Degrade gracefully",
                    "expected_output": "Queued retry",
                }
            ],
        },
    ]


def stub_allocations() -> list[dict]:
    return [
        {
            "step_id": 1,
            "step_name": "Validate Payload & Auth",
            "description": "Deterministic schema and auth checks",
            "allocated_tier": TierType.TIER_1_CODE,
            "rationale": "Strict validation must be deterministic",
            "suggested_tech": "Pydantic + HMAC",
        },
        {
            "step_id": 2,
            "step_name": "Search Knowledge Base",
            "description": "Semantic retrieval over structured corpus",
            "allocated_tier": TierType.TIER_2_CLASSICAL_ML,
            "rationale": "Embedding similarity is Tier 2",
            "suggested_tech": "Sentence-Transformers + cosine",
        },
        {
            "step_id": 3,
            "step_name": "Reason & Draft Reply",
            "description": "Open-ended synthesis",
            "allocated_tier": TierType.TIER_3_LLM_AGENT,
            "rationale": "Unstructured generation requires LLM",
            "suggested_tech": "LangGraph + qwen2.5-coder",
        },
        {
            "step_id": 4,
            "step_name": "Post-execution Gates & Emit",
            "description": "PII and budget gates before emit",
            "allocated_tier": TierType.TIER_1_CODE,
            "rationale": "Safety gates are deterministic",
            "suggested_tech": "Regex PII + budget counter",
        },
    ]


def stub_file_map(project_name: str) -> dict[str, str]:
    safe = project_name.replace(" ", "_").lower() or "project"
    return {
        "config.json": '{"project": "%s"}' % safe,
        "state.py": "from pydantic import BaseModel\n\nclass AgentState(BaseModel):\n    pass\n",
        "graph.py": "# LangGraph StateGraph stub\n",
        "main.py": "def main():\n    print('hello from scaffold')\n",
        "test_workflow.py": "def test_smoke():\n    assert True\n",
        "Dockerfile": "FROM python:3.12-slim\n",
        "README.md": f"# {project_name}\n\nGenerated by MetaAgent Studio.\n",
        "agents/__init__.py": "",
        "tools/__init__.py": "",
        "gates/__init__.py": "",
    }
