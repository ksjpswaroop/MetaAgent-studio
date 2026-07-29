from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    AgentSpec,
    ArchitectureBlueprint,
    StepAllocation,
    StudioSession,
    ToolSpec,
)
from app.services.llm.client import chat_json
from app.services.session_helpers import append_event, load_state, save_state
from app.utils.ids import new_id
from app.utils.time import utc_now


def _fallback_blueprint(allocations: list[StepAllocation]) -> dict:
    agents = []
    for a in allocations or []:
        agents.append(
            {
                "name": a.step_name or "Worker",
                "role": a.description or a.step_name or "Process step",
                "system_prompt": f"You handle: {a.step_name}",
                "tools": [],
                "model_recommendation": "8B",
            }
        )
    if not agents:
        agents = [
            {
                "name": "Coordinator",
                "role": "Orchestrate the workflow",
                "system_prompt": "Coordinate the helper end to end.",
                "tools": ["http_get"],
                "model_recommendation": "8B",
            }
        ]
    return {
        "agent_state_schema": {"fields": ["input", "result", "status"]},
        "graph_topology": {"nodes": [a["name"] for a in agents], "edges": []},
        "model_notes": "Demo fallback blueprint",
        "agents": agents,
        "tools": [
            {
                "name": "http_get",
                "description": "Read-only HTTP GET",
                "is_side_effecting": False,
                "side_effect_class": "read_only",
                "parameters": {"url": "string"},
                "timeout_seconds": 30.0,
            }
        ],
    }


def _normalize_blueprint(data: dict | None, allocations: list[StepAllocation]) -> dict:
    fb = _fallback_blueprint(allocations)
    if not isinstance(data, dict):
        return fb
    agents_in = data.get("agents") or []
    agents = []
    for i, agent in enumerate(agents_in):
        if not isinstance(agent, dict):
            continue
        name = agent.get("name") or agent.get("role") or f"Agent {i + 1}"
        tool_names: list[str] = []
        for t in agent.get("tools") or []:
            if isinstance(t, str) and t.strip():
                tool_names.append(t.strip())
            elif isinstance(t, dict):
                tn = t.get("name") or t.get("id")
                if tn:
                    tool_names.append(str(tn))
        agents.append(
            {
                "name": str(name),
                "role": str(agent.get("role") or name),
                "system_prompt": str(agent.get("system_prompt") or ""),
                "tools": tool_names,
                "model_recommendation": str(agent.get("model_recommendation") or "8B"),
            }
        )
    tools_in = data.get("tools") or []
    tools = []
    for i, tool in enumerate(tools_in):
        if not isinstance(tool, dict):
            continue
        name = tool.get("name") or f"tool_{i}"
        tools.append(
            {
                "name": str(name),
                "description": str(tool.get("description") or ""),
                "is_side_effecting": bool(tool.get("is_side_effecting")),
                "side_effect_class": tool.get("side_effect_class")
                or ("side_effecting" if tool.get("is_side_effecting") else "read_only"),
                "parameters": tool.get("parameters") or {},
                "timeout_seconds": float(tool.get("timeout_seconds") or 30.0),
            }
        )
    return {
        "agent_state_schema": data.get("agent_state_schema") or fb["agent_state_schema"],
        "graph_topology": data.get("graph_topology") or fb["graph_topology"],
        "model_notes": str(data.get("model_notes") or ""),
        "agents": agents or fb["agents"],
        "tools": tools or fb["tools"],
    }


async def build_architecture(
    db: AsyncSession, session: StudioSession
) -> ArchitectureBlueprint:
    allocations = list(
        (
            await db.scalars(
                select(StepAllocation)
                .where(StepAllocation.session_id == session.id)
                .order_by(StepAllocation.step_id.asc())
            )
        ).all()
    )
    try:
        raw = await chat_json(
            db,
            task="architecture_build",
            system=(
                "You are SystemArchitectAgent. Return JSON with agents "
                "[{name,role,system_prompt,tools,model_recommendation}] and tools "
                "[{name,description,is_side_effecting,parameters,timeout_seconds}]. "
                "Each agent.tools MUST be an array of tool name strings only "
                "(e.g. [\"http_get\"]), never tool objects."
            ),
            user=json.dumps(
                [
                    {
                        "step_id": a.step_id,
                        "name": a.step_name,
                        "tier": a.allocated_tier,
                        "tech": a.suggested_tech,
                    }
                    for a in allocations
                ]
            ),
        )
    except Exception:
        raw = {}
    data = _normalize_blueprint(raw if isinstance(raw, dict) else None, allocations)

    existing = await db.scalar(
        select(ArchitectureBlueprint).where(
            ArchitectureBlueprint.session_id == session.id
        )
    )
    if existing:
        await db.delete(existing)
        await db.flush()

    bp = ArchitectureBlueprint(
        id=new_id("bp"),
        session_id=session.id,
        agent_state_schema_json=json.dumps(data.get("agent_state_schema") or {}),
        graph_topology_json=json.dumps(data.get("graph_topology") or {}),
        model_notes=data.get("model_notes") or "",
        created_at=utc_now(),
    )
    db.add(bp)
    await db.flush()
    for idx, agent in enumerate(data.get("agents") or []):
        db.add(
            AgentSpec(
                id=new_id("agent"),
                blueprint_id=bp.id,
                name=agent["name"],
                role=agent.get("role", ""),
                system_prompt=agent.get("system_prompt", ""),
                tools_json=json.dumps(agent.get("tools") or []),
                model_recommendation=agent.get("model_recommendation", ""),
                sort_order=idx,
            )
        )
    for tool in data.get("tools") or []:
        side = tool.get("side_effect_class") or (
            "side_effecting" if tool.get("is_side_effecting") else "read_only"
        )
        db.add(
            ToolSpec(
                id=new_id("tool"),
                blueprint_id=bp.id,
                name=tool["name"],
                description=tool.get("description", ""),
                is_side_effecting=bool(tool.get("is_side_effecting")),
                side_effect_class=side,
                parameters_json=json.dumps(tool.get("parameters") or {}),
                timeout_seconds=float(tool.get("timeout_seconds") or 30.0),
            )
        )
    session.stage = "architected"
    state = load_state(session)
    state["agent_specs"] = data.get("agents") or []
    state["tool_specs"] = data.get("tools") or []
    save_state(session, state)
    await append_event(db, session.id, "architecture.built")
    return (
        await db.scalar(
            select(ArchitectureBlueprint)
            .where(ArchitectureBlueprint.id == bp.id)
            .options(
                selectinload(ArchitectureBlueprint.agents),
                selectinload(ArchitectureBlueprint.tools),
            )
        )
    ) or bp
