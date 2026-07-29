from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ArchitectureBlueprint, StepAllocation
from app.db.session import get_db
from app.models.schemas import AgentSpecOut, ArchitectureBlueprintOut, ToolSpecOut
from app.services import architecture_engine
from app.services.session_helpers import get_session_or_404

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


def _tool_names(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
        elif isinstance(item, dict):
            name = item.get("name") or item.get("tool") or item.get("id")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
    return names


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
                tools=_tool_names(json.loads(a.tools_json or "[]")),
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
    bp = await architecture_engine.build_architecture(db, session)
    await db.commit()
    loaded = await _load_blueprint(db, session_id)
    assert loaded is not None
    return _out(loaded)


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
    return (await get_architecture(session_id, db)).agents


@router.get("/{session_id}/tools", response_model=list[ToolSpecOut])
async def list_tools(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ToolSpecOut]:
    return (await get_architecture(session_id, db)).tools


@router.get("/{session_id}/state-schema")
async def state_schema(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> dict:
    return (await get_architecture(session_id, db)).agent_state_schema
