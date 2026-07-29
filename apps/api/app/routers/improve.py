from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentPack, ImprovementIteration, Project, StudioSession
from app.db.session import get_db
from app.models.schemas import (
    AgentPackOut,
    ForkPackRequest,
    ImproveIterateRequest,
    ImprovementIterationOut,
    PublishPackRequest,
    StudioSessionOut,
)
from app.services import improve_engine
from app.services.session_helpers import get_session_or_404, load_state
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(tags=["improve"])


def _iter_out(row: ImprovementIteration) -> ImprovementIterationOut:
    return ImprovementIterationOut(
        id=row.id,
        session_id=row.session_id,
        iteration_index=row.iteration_index,
        simulation_run_id=row.simulation_run_id,
        package_id=row.package_id,
        score_before=row.score_before,
        score_after=row.score_after,
        plateau=bool(row.plateau),
        notes=row.notes,
        details=json.loads(row.details_json or "{}"),
        created_at=row.created_at,
    )


def _pack_out(p: AgentPack) -> AgentPackOut:
    return AgentPackOut(
        id=p.id,
        name=p.name,
        source_session_id=p.source_session_id,
        source_project_id=p.source_project_id,
        package_id=p.package_id,
        blueprint=json.loads(p.blueprint_json or "{}"),
        best_score=p.best_score,
        scores=json.loads(p.scores_json or "{}"),
        metadata=json.loads(p.metadata_json or "{}"),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.post("/api/v1/improve/{session_id}/iterate", response_model=ImprovementIterationOut)
async def iterate(
    session_id: str,
    body: ImproveIterateRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ImprovementIterationOut:
    body = body or ImproveIterateRequest()
    session = await get_session_or_404(db, session_id)
    row = await improve_engine.iterate(
        db,
        session,
        auto_attach_edge_cases=body.auto_attach_edge_cases,
        generate_prompts=body.generate_prompts,
        tool_target=body.tool_target,
    )
    await db.commit()
    await db.refresh(row)
    return _iter_out(row)


@router.get("/api/v1/improve/{session_id}/history", response_model=list[ImprovementIterationOut])
async def history(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ImprovementIterationOut]:
    await get_session_or_404(db, session_id)
    rows = (
        await db.scalars(
            select(ImprovementIteration)
            .where(ImprovementIteration.session_id == session_id)
            .order_by(ImprovementIteration.iteration_index.asc())
        )
    ).all()
    return [_iter_out(r) for r in rows]


@router.post("/api/v1/improve/{session_id}/publish-local", response_model=AgentPackOut)
async def publish_local(
    session_id: str,
    body: PublishPackRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentPackOut:
    session = await get_session_or_404(db, session_id)
    pack = await improve_engine.publish_pack(
        db, session, name=body.name, package_id=body.package_id
    )
    await db.commit()
    await db.refresh(pack)
    return _pack_out(pack)


@router.get("/api/v1/packs", response_model=list[AgentPackOut])
async def list_packs(db: AsyncSession = Depends(get_db)) -> list[AgentPackOut]:
    rows = (
        await db.scalars(select(AgentPack).order_by(AgentPack.created_at.desc()))
    ).all()
    return [_pack_out(r) for r in rows]


@router.post("/api/v1/packs/{pack_id}/fork", response_model=StudioSessionOut)
async def fork_pack(
    pack_id: str,
    body: ForkPackRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> StudioSessionOut:
    body = body or ForkPackRequest()
    pack = await db.get(AgentPack, pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Pack not found")
    now = utc_now()
    project = Project(
        id=new_id("proj"),
        name=body.project_name or f"{pack.name} Fork",
        description=f"Forked from agent pack {pack.id}",
        status="draft",
        export_path=None,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    await db.flush()
    prompt = body.raw_user_prompt or f"Improve and reuse agent pack: {pack.name}"
    session = StudioSession(
        id=new_id("sess"),
        project_id=project.id,
        stage="created",
        raw_user_prompt=prompt,
        flow_approved=False,
        state_json=json.dumps(
            {
                "session_id": None,
                "raw_user_prompt": prompt,
                "forked_pack_id": pack.id,
                "blueprint_seed": json.loads(pack.blueprint_json or "{}"),
                "scope_envelope": None,
                "sample_flows": [],
                "flow_approved": False,
                "allocations": [],
                "agent_specs": [],
                "tool_specs": [],
                "generated_files": {},
            }
        ),
        token_usage=0,
        created_at=now,
        updated_at=now,
    )
    state = json.loads(session.state_json)
    state["session_id"] = session.id
    session.state_json = json.dumps(state)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return StudioSessionOut(
        id=session.id,
        project_id=session.project_id,
        stage=session.stage,
        raw_user_prompt=session.raw_user_prompt,
        flow_approved=bool(session.flow_approved),
        state=load_state(session),
        token_usage=session.token_usage,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
