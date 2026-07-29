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


async def build_architecture(
    db: AsyncSession, session: StudioSession
) -> ArchitectureBlueprint:
    allocations = (
        await db.scalars(
            select(StepAllocation)
            .where(StepAllocation.session_id == session.id)
            .order_by(StepAllocation.step_id.asc())
        )
    ).all()
    data = await chat_json(
        db,
        task="architecture_build",
        system="You are SystemArchitectAgent. Return blueprint JSON with agents and tools.",
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
    await db.flush()
    loaded = await db.scalar(
        select(ArchitectureBlueprint)
        .where(ArchitectureBlueprint.id == bp.id)
        .options(
            selectinload(ArchitectureBlueprint.agents),
            selectinload(ArchitectureBlueprint.tools),
        )
    )
    assert loaded is not None
    return loaded
