from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    AgentPack,
    ArchitectureBlueprint,
    ImprovementIteration,
    Package,
    StudioSession,
)
from app.services import edge_case_engine, package_engine, prompt_engine, simulation_engine
from app.services.session_helpers import append_event
from app.utils.ids import new_id
from app.utils.time import utc_now


async def iterate(
    db: AsyncSession,
    session: StudioSession,
    *,
    auto_attach_edge_cases: bool = True,
    generate_prompts: bool = True,
    tool_target: str = "cursor",
) -> ImprovementIteration:
    prior = (
        await db.scalars(
            select(ImprovementIteration)
            .where(ImprovementIteration.session_id == session.id)
            .order_by(ImprovementIteration.iteration_index.desc())
        )
    ).first()
    score_before = prior.score_after if prior else 0.0
    next_idx = (prior.iteration_index + 1) if prior else 1

    edges = await edge_case_engine.generate_edge_cases(db, session, count=3)
    if auto_attach_edge_cases:
        for e in edges:
            await edge_case_engine.attach_edge_case(db, session, e)

    run = await simulation_engine.run_simulation(
        db,
        session,
        edge_case_ids=[e.id for e in edges],
        include_all_scenarios=True,
    )
    score = json.loads(run.score_json or "{}")
    score_after = float(score.get("overall") or 0.0)

    prompts = []
    if generate_prompts:
        prompts = await prompt_engine.generate_prompts(
            db, session, simulation_run_id=run.id, tool_target=tool_target
        )

    pkg = await package_engine.build_package(db, session, run_verify=True)
    plateau = bool(prior and score_after <= (score_before or 0.0) + 0.01)

    # Small hill-climb nudge: if failing, bump notes with prompt count
    notes = (
        f"sim={run.status} score {score_before}->{score_after}; "
        f"edges={len(edges)} prompts={len(prompts)} package={pkg.status}"
    )
    row = ImprovementIteration(
        id=new_id("iter"),
        session_id=session.id,
        iteration_index=next_idx,
        simulation_run_id=run.id,
        package_id=pkg.id,
        score_before=score_before,
        score_after=score_after,
        plateau=plateau,
        notes=notes,
        details_json=json.dumps(
            {
                "edge_case_ids": [e.id for e in edges],
                "prompt_ids": [p.id for p in prompts],
                "score": score,
            }
        ),
        created_at=utc_now(),
    )
    db.add(row)
    await append_event(
        db,
        session.id,
        "improve.iterated",
        {"iteration": next_idx, "score_after": score_after, "plateau": plateau},
    )
    return row


async def publish_pack(
    db: AsyncSession, session: StudioSession, name: str, package_id: str | None = None
) -> AgentPack:
    pkg = None
    if package_id:
        pkg = await db.get(Package, package_id)
    if pkg is None:
        pkg = await db.scalar(
            select(Package)
            .where(Package.session_id == session.id)
            .order_by(Package.created_at.desc())
        )
    bp = await db.scalar(
        select(ArchitectureBlueprint)
        .where(ArchitectureBlueprint.session_id == session.id)
        .options(
            selectinload(ArchitectureBlueprint.agents),
            selectinload(ArchitectureBlueprint.tools),
        )
    )
    blueprint = {}
    if bp:
        blueprint = {
            "agent_state_schema": json.loads(bp.agent_state_schema_json or "{}"),
            "graph_topology": json.loads(bp.graph_topology_json or "{}"),
            "agents": [
                {
                    "name": a.name,
                    "role": a.role,
                    "system_prompt": a.system_prompt,
                    "tools": json.loads(a.tools_json or "[]"),
                    "model_recommendation": a.model_recommendation,
                }
                for a in bp.agents
            ],
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "side_effect_class": t.side_effect_class,
                    "timeout_seconds": t.timeout_seconds,
                }
                for t in bp.tools
            ],
        }
    latest_iter = (
        await db.scalars(
            select(ImprovementIteration)
            .where(ImprovementIteration.session_id == session.id)
            .order_by(ImprovementIteration.iteration_index.desc())
        )
    ).first()
    best = float(latest_iter.score_after or 0.0) if latest_iter else 0.0
    now = utc_now()
    pack = AgentPack(
        id=new_id("pack"),
        name=name,
        source_session_id=session.id,
        source_project_id=session.project_id,
        package_id=pkg.id if pkg else None,
        blueprint_json=json.dumps(blueprint),
        best_score=best,
        scores_json=json.dumps(
            {"best": best, "last_iteration": latest_iter.iteration_index if latest_iter else 0}
        ),
        metadata_json=json.dumps({"published_at": now}),
        created_at=now,
        updated_at=now,
    )
    db.add(pack)
    await append_event(db, session.id, "packs.published", {"pack_id": pack.id, "name": name})
    return pack
