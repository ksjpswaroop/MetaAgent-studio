from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AgentSpec, ArchitectureBlueprint, StepAllocation, ToolSpec
from app.db.session import get_db
from app.models.schemas import AgentSpecOut, ArchitectureBlueprintOut, ToolSpecOut
from app.services.session_helpers import (
    append_event,
    get_session_or_404,
    load_state,
    save_state,
)
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/architecture", tags=["architecture"])


async def _load_blueprint(
    db: AsyncSession, session_id: str
) -> ArchitectureBlueprint | None:
    return await db.scalar(
        select(ArchitectureBlueprint)
        .where(ArchitectureBlueprint.session_id == session_id)
        .options(
            selectinload(ArchitectureBlueprint.agents),
            selectinload(ArchitectureBlueprint.tools),
        )
    )


def _out(bp: ArchitectureBlueprint) -> ArchitectureBlueprintOut:
    agents = sorted(bp.agents, key=lambda a: a.sort_order)
    return ArchitectureBlueprintOut(
        id=bp.id,
        session_id=bp.session_id,
        agent_state_schema=json.loads(bp.agent_state_schema_json or "{}"),
        graph_topology=json.loads(bp.graph_topology_json or "{}"),
        model_notes=bp.model_notes,
        agents=[
            AgentSpecOut(
                id=a.id,
                name=a.name,
                role=a.role,
                system_prompt=a.system_prompt,
                tools=json.loads(a.tools_json or "[]"),
                model_recommendation=a.model_recommendation,
            )
            for a in agents
        ],
        tools=[
            ToolSpecOut(
                id=t.id,
                name=t.name,
                description=t.description,
                is_side_effecting=bool(t.is_side_effecting),
                side_effect_class=t.side_effect_class,
                parameters=json.loads(t.parameters_json or "{}"),
                timeout_seconds=t.timeout_seconds,
            )
            for t in bp.tools
        ],
    )


@router.post("/{session_id}/build", response_model=ArchitectureBlueprintOut)
async def build_architecture(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> ArchitectureBlueprintOut:
    session = await get_session_or_404(db, session_id)
    allocations = (
        await db.scalars(
            select(StepAllocation).where(StepAllocation.session_id == session_id)
        )
    ).all()
    if not allocations:
        raise HTTPException(status_code=409, detail="Run allocation first")

    existing = await _load_blueprint(db, session_id)
    if existing:
        await db.delete(existing)
        await db.flush()

    schema = {
        "title": "AgentState",
        "type": "object",
        "properties": {
            "input_payload": {"type": "object"},
            "retrieved_context": {"type": "array", "items": {"type": "string"}},
            "draft": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
        },
    }
    topology = {
        "nodes": ["validate", "retrieve", "reason", "emit"],
        "edges": [
            ["validate", "retrieve"],
            ["retrieve", "reason"],
            ["reason", "emit"],
        ],
    }
    bp = ArchitectureBlueprint(
        id=new_id("bp"),
        session_id=session_id,
        agent_state_schema_json=json.dumps(schema),
        graph_topology_json=json.dumps(topology),
        model_notes="Stub blueprint from allocations",
        created_at=utc_now(),
    )
    db.add(bp)
    await db.flush()

    agents = [
        AgentSpec(
            id=new_id("agent"),
            blueprint_id=bp.id,
            name="RequirementsValidator",
            role="Tier 1 validation",
            system_prompt="Validate inputs; output JSON only.",
            tools_json=json.dumps(["validate_schema"]),
            model_recommendation="n/a-code",
            sort_order=0,
        ),
        AgentSpec(
            id=new_id("agent"),
            blueprint_id=bp.id,
            name="RetrievalSpecialist",
            role="Tier 2 retrieval",
            system_prompt="Rank context snippets.",
            tools_json=json.dumps(["search_kb"]),
            model_recommendation="embeddings",
            sort_order=1,
        ),
        AgentSpec(
            id=new_id("agent"),
            blueprint_id=bp.id,
            name="DraftSynthesizer",
            role="Tier 3 synthesis",
            system_prompt="Draft responses from context. Strip markdown fences from JSON.",
            tools_json=json.dumps(["emit_message"]),
            model_recommendation="qwen2.5-coder:7b",
            sort_order=2,
        ),
    ]
    tools = [
        ToolSpec(
            id=new_id("tool"),
            blueprint_id=bp.id,
            name="validate_schema",
            description="Validate payload against Pydantic model",
            is_side_effecting=False,
            side_effect_class="read_only",
            parameters_json=json.dumps({"schema": "AgentState"}),
            timeout_seconds=30.0,
        ),
        ToolSpec(
            id=new_id("tool"),
            blueprint_id=bp.id,
            name="search_kb",
            description="Vector similarity search",
            is_side_effecting=False,
            side_effect_class="read_only",
            parameters_json=json.dumps({"top_k": 5}),
            timeout_seconds=30.0,
        ),
        ToolSpec(
            id=new_id("tool"),
            blueprint_id=bp.id,
            name="emit_message",
            description="Send outbound message",
            is_side_effecting=True,
            side_effect_class="side_effecting",
            parameters_json=json.dumps({"channel": "email"}),
            timeout_seconds=30.0,
        ),
    ]
    for a in agents:
        db.add(a)
    for t in tools:
        db.add(t)

    session.stage = "architected"
    state = load_state(session)
    state["agent_specs"] = [{"name": a.name, "role": a.role} for a in agents]
    state["tool_specs"] = [
        {"name": t.name, "side_effect_class": t.side_effect_class} for t in tools
    ]
    save_state(session, state)
    await append_event(db, session_id, "architecture.built")
    await db.commit()
    bp2 = await _load_blueprint(db, session_id)
    assert bp2 is not None
    return _out(bp2)


@router.get("/{session_id}", response_model=ArchitectureBlueprintOut)
async def get_architecture(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> ArchitectureBlueprintOut:
    await get_session_or_404(db, session_id)
    bp = await _load_blueprint(db, session_id)
    if bp is None:
        raise HTTPException(status_code=404, detail="Blueprint not built")
    return _out(bp)


@router.get("/{session_id}/agents", response_model=list[AgentSpecOut])
async def list_agents(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[AgentSpecOut]:
    bp = await get_architecture(session_id, db)
    return bp.agents


@router.get("/{session_id}/tools", response_model=list[ToolSpecOut])
async def list_tools(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ToolSpecOut]:
    bp = await get_architecture(session_id, db)
    return bp.tools


@router.get("/{session_id}/state-schema")
async def state_schema(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> dict:
    bp = await get_architecture(session_id, db)
    return bp.agent_state_schema
