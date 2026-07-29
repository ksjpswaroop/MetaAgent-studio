from __future__ import annotations

import json
import time
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import LlmProvider, ProviderHealthCheck
from app.services.llm import adapters
from app.services.llm.cassettes import load_cassette, save_cassette
from app.services.llm.parsing import parse_json_content
from app.utils.ids import new_id
from app.utils.time import utc_now


async def _providers(db: AsyncSession) -> list[LlmProvider]:
    return list(
        (
            await db.scalars(
                select(LlmProvider)
                .where(LlmProvider.enabled.is_(True))
                .order_by(LlmProvider.priority.asc())
            )
        ).all()
    )


async def chat_json(
    db: AsyncSession,
    *,
    task: str,
    system: str,
    user: str,
    schema_hint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call LLM and return parsed JSON. Uses cassettes when METAAGENT_LLM_MODE=cassette."""
    if settings.llm_mode == "cassette":
        cached = load_cassette(task, user)
        if cached is not None:
            return cached
        # Deterministic synthetic fallback for unknown cassette keys
        synthetic = _synthetic(task, user, schema_hint)
        save_cassette(task, user, synthetic)
        return synthetic

    providers = await _providers(db)
    if not providers:
        raise HTTPException(status_code=503, detail="No enabled LLM providers")

    errors: list[str] = []
    for prov in providers:
        started = time.perf_counter()
        try:
            raw = await _dispatch(prov, system, user)
            parsed = parse_json_content(raw)
            if not isinstance(parsed, dict):
                raise ValueError("LLM JSON root must be an object")
            latency = int((time.perf_counter() - started) * 1000)
            db.add(
                ProviderHealthCheck(
                    id=new_id("phc"),
                    provider_id=prov.id,
                    ok=True,
                    latency_ms=latency,
                    message=f"chat_json:{task}",
                    checked_at=utc_now(),
                )
            )
            await db.commit()
            if settings.llm_mode == "live_record":
                save_cassette(task, user, parsed)
            return parsed
        except Exception as exc:  # noqa: BLE001
            latency = int((time.perf_counter() - started) * 1000)
            errors.append(f"{prov.name}: {exc}")
            db.add(
                ProviderHealthCheck(
                    id=new_id("phc"),
                    provider_id=prov.id,
                    ok=False,
                    latency_ms=latency,
                    message=str(exc)[:500],
                    checked_at=utc_now(),
                )
            )
            await db.commit()

    raise HTTPException(
        status_code=503,
        detail="All LLM providers failed: " + "; ".join(errors),
    )


async def _dispatch(prov: LlmProvider, system: str, user: str) -> str:
    base = prov.base_url or ""
    model = prov.default_model
    if prov.name == "ollama":
        return await adapters.call_ollama(base, model, system, user)
    if prov.name == "anthropic":
        return await adapters.call_anthropic(
            base, model, system, user, prov.api_key_env_var
        )
    return await adapters.call_openai_compat(
        base, model, system, user, prov.api_key_env_var
    )


def _synthetic(task: str, user: str, schema_hint: dict[str, Any] | None) -> dict[str, Any]:
    """Offline defaults so cassette mode always works without pre-recorded files."""
    if task == "discovery_questions":
        return {
            "questions": [
                {
                    "question_key": "trigger_type",
                    "content": "How is this system triggered? (webhook / cron / manual)",
                },
                {
                    "question_key": "external_tools",
                    "content": "Which external systems are required?",
                },
                {
                    "question_key": "human_in_loop",
                    "content": "Should a human review before side-effects? (yes/no)",
                },
                {
                    "question_key": "fallback_strategy",
                    "content": "What happens when an external service fails?",
                },
            ]
        }
    if task == "discovery_finalize":
        return {
            "project_name": "Generated Project",
            "primary_goal": user[:200] or "Automate workflow",
            "trigger_type": "webhook",
            "external_tools": ["http_api"],
            "human_in_loop": True,
            "fallback_strategy": "queue and retry",
        }
    if task == "flows_generate":
        return {
            "scenarios": [
                {
                    "kind": "happy",
                    "title": "Scenario A: Happy Path",
                    "ascii_flow": "Validate -> Retrieve -> Reason -> Emit",
                    "mermaid_flow": "flowchart LR\n  A-->B-->C-->D",
                    "steps": [
                        {
                            "step_index": 1,
                            "name": "Validate Payload & Auth",
                            "processing_goal": "Schema validation",
                            "expected_output": "Valid event",
                            "input_data": {},
                        },
                        {
                            "step_index": 2,
                            "name": "Search Knowledge Base",
                            "processing_goal": "Retrieve context",
                            "expected_output": "Snippets",
                            "input_data": {},
                        },
                        {
                            "step_index": 3,
                            "name": "Reason & Draft Reply",
                            "processing_goal": "Synthesize",
                            "expected_output": "Draft",
                            "input_data": {},
                        },
                        {
                            "step_index": 4,
                            "name": "Post-execution Gates & Emit",
                            "processing_goal": "Safety gates",
                            "expected_output": "Safe message",
                            "input_data": {},
                        },
                    ],
                },
                {
                    "kind": "ambiguity",
                    "title": "Scenario B: High Ambiguity",
                    "ascii_flow": "Validate -> Clarify",
                    "mermaid_flow": "flowchart LR\n  A-->E",
                    "steps": [
                        {
                            "step_index": 1,
                            "name": "Validate Payload & Auth",
                            "processing_goal": "Schema validation",
                            "expected_output": "Valid event",
                            "input_data": {},
                        },
                        {
                            "step_index": 2,
                            "name": "Clarify Missing Fields",
                            "processing_goal": "Ask user",
                            "expected_output": "Question",
                            "input_data": {"missing": ["id"]},
                        },
                    ],
                },
                {
                    "kind": "failure",
                    "title": "Scenario C: External Failure",
                    "ascii_flow": "Validate -> Fallback",
                    "mermaid_flow": "flowchart LR\n  A-->F",
                    "steps": [
                        {
                            "step_index": 1,
                            "name": "Validate Payload & Auth",
                            "processing_goal": "Schema validation",
                            "expected_output": "Valid event",
                            "input_data": {},
                        },
                        {
                            "step_index": 2,
                            "name": "Fallback Cache / Queue",
                            "processing_goal": "Degrade",
                            "expected_output": "Queued",
                            "input_data": {"error": "timeout"},
                        },
                    ],
                },
            ]
        }
    if task == "allocation_run":
        return {
            "allocations": [
                {
                    "step_id": 1,
                    "step_name": "Validate Payload & Auth",
                    "description": "Deterministic checks",
                    "allocated_tier": "TIER_1_CODE",
                    "rationale": "Strict validation",
                    "suggested_tech": "Pydantic + HMAC",
                },
                {
                    "step_id": 2,
                    "step_name": "Search Knowledge Base",
                    "description": "Retrieval",
                    "allocated_tier": "TIER_2_CLASSICAL_ML",
                    "rationale": "Embeddings search",
                    "suggested_tech": "Sentence-Transformers",
                },
                {
                    "step_id": 3,
                    "step_name": "Reason & Draft Reply",
                    "description": "Synthesis",
                    "allocated_tier": "TIER_3_LLM_AGENT",
                    "rationale": "Open-ended generation",
                    "suggested_tech": "LangGraph + Ollama",
                },
                {
                    "step_id": 4,
                    "step_name": "Post-execution Gates & Emit",
                    "description": "Gates",
                    "allocated_tier": "TIER_1_CODE",
                    "rationale": "Safety must be deterministic",
                    "suggested_tech": "Regex + budget",
                },
            ]
        }
    if task == "architecture_build":
        return {
            "agent_state_schema": {
                "title": "AgentState",
                "type": "object",
                "properties": {
                    "input_payload": {"type": "object"},
                    "retrieved_context": {"type": "array"},
                    "draft": {"type": "string"},
                    "errors": {"type": "array"},
                },
            },
            "graph_topology": {
                "nodes": ["validate", "retrieve", "reason", "emit"],
                "edges": [["validate", "retrieve"], ["retrieve", "reason"], ["reason", "emit"]],
            },
            "model_notes": "LLM-generated architecture",
            "agents": [
                {
                    "name": "RequirementsValidator",
                    "role": "Tier 1 validation",
                    "system_prompt": "Validate inputs; output JSON only. Strip markdown fences.",
                    "tools": ["validate_schema"],
                    "model_recommendation": "n/a-code",
                },
                {
                    "name": "RetrievalSpecialist",
                    "role": "Tier 2 retrieval",
                    "system_prompt": "Rank context snippets.",
                    "tools": ["search_kb"],
                    "model_recommendation": "embeddings",
                },
                {
                    "name": "DraftSynthesizer",
                    "role": "Tier 3 synthesis",
                    "system_prompt": "Draft responses from context.",
                    "tools": ["emit_message"],
                    "model_recommendation": "qwen2.5-coder:7b",
                },
            ],
            "tools": [
                {
                    "name": "validate_schema",
                    "description": "Validate payload",
                    "is_side_effecting": False,
                    "side_effect_class": "read_only",
                    "parameters": {"schema": "AgentState"},
                    "timeout_seconds": 30,
                },
                {
                    "name": "search_kb",
                    "description": "Vector search",
                    "is_side_effecting": False,
                    "side_effect_class": "read_only",
                    "parameters": {"top_k": 5},
                    "timeout_seconds": 30,
                },
                {
                    "name": "emit_message",
                    "description": "Send outbound message",
                    "is_side_effecting": True,
                    "side_effect_class": "side_effecting",
                    "parameters": {"channel": "email"},
                    "timeout_seconds": 30,
                },
            ],
        }
    if task == "edge_cases":
        return {
            "edge_cases": [
                {
                    "category": "timeout",
                    "title": "KB timeout",
                    "description": "Search Knowledge Base exceeds timeout",
                    "agent_name": "RetrievalSpecialist",
                    "step_name": "Search Knowledge Base",
                    "input_fixture": {"query": "x", "force_timeout": True},
                    "expected_behavior": "Fallback queue",
                },
                {
                    "category": "partial_data",
                    "title": "Missing customer_id",
                    "description": "Payload missing required id",
                    "agent_name": "RequirementsValidator",
                    "step_name": "Validate Payload & Auth",
                    "input_fixture": {"payload": {}},
                    "expected_behavior": "Clarify missing fields",
                },
                {
                    "category": "schema_drift",
                    "title": "Unexpected nested field",
                    "description": "Extra unknown keys in payload",
                    "agent_name": "RequirementsValidator",
                    "step_name": "Validate Payload & Auth",
                    "input_fixture": {"payload": {"extra": True}},
                    "expected_behavior": "Reject or strip extras",
                },
                {
                    "category": "tool_failure",
                    "title": "Emit channel down",
                    "description": "Outbound channel 503",
                    "agent_name": "DraftSynthesizer",
                    "step_name": "Post-execution Gates & Emit",
                    "input_fixture": {"draft": "hi", "emit_fail": True},
                    "expected_behavior": "Retry with backoff",
                },
            ]
        }
    if task == "coding_gap_prompts":
        return {
            "prompts": [
                {
                    "title": "Handle KB timeout in retrieval node",
                    "gap_description": "Simulation failed on Search Knowledge Base timeout",
                    "files": ["tools/search_kb.py", "graph.py", "gates/pre_tool.py"],
                    "acceptance_criteria": "Timeouts raise typed error and route to fallback node; pytest covers timeout fixture",
                    "prompt_text": (
                        "You are implementing a LangGraph retrieval node. "
                        "Add timeout handling with fallback routing. "
                        "Files: tools/search_kb.py, graph.py. "
                        "Acceptance: pytest for timeout fixture passes."
                    ),
                }
            ]
        }
    if schema_hint:
        return dict(schema_hint)
    return {"ok": True, "task": task, "echo": user[:120]}
