from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SimulationRun, SimulationStepTrace
from app.db.session import get_db
from app.models.schemas import (
    SimulationRunOut,
    SimulationRunRequest,
    SimulationScore,
    SimulationTraceOut,
)
from app.services import simulation_engine
from app.services.session_helpers import get_session_or_404

router = APIRouter(prefix="/api/v1/simulate", tags=["simulate"])


def _run_out(run: SimulationRun, traces: list[SimulationStepTrace] | None = None) -> SimulationRunOut:
    score_raw = json.loads(run.score_json or "{}")
    return SimulationRunOut(
        id=run.id,
        session_id=run.session_id,
        status=run.status,
        scenario_ids=json.loads(run.scenario_ids_json or "[]"),
        edge_case_ids=json.loads(run.edge_case_ids_json or "[]"),
        score=SimulationScore(**{**SimulationScore().model_dump(), **score_raw}),
        summary=run.summary,
        traces=[
            SimulationTraceOut(
                id=t.id,
                step_index=t.step_index,
                step_name=t.step_name,
                agent_name=t.agent_name,
                input=json.loads(t.input_json or "{}"),
                output=json.loads(t.output_json or "{}"),
                passed=bool(t.passed),
                latency_ms=t.latency_ms,
                error=t.error,
            )
            for t in (traces or [])
        ],
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )


@router.post("/{session_id}/run", response_model=SimulationRunOut)
async def run_sim(
    session_id: str,
    body: SimulationRunRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> SimulationRunOut:
    body = body or SimulationRunRequest()
    session = await get_session_or_404(db, session_id)
    run = await simulation_engine.run_simulation(
        db,
        session,
        scenario_ids=body.scenario_ids or None,
        edge_case_ids=body.edge_case_ids or None,
        include_all_scenarios=body.include_all_scenarios,
    )
    await db.commit()
    traces = list(
        (
            await db.scalars(
                select(SimulationStepTrace)
                .where(SimulationStepTrace.run_id == run.id)
                .order_by(SimulationStepTrace.step_index.asc())
            )
        ).all()
    )
    return _run_out(run, traces)


@router.get("/{session_id}/runs", response_model=list[SimulationRunOut])
async def list_runs(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[SimulationRunOut]:
    await get_session_or_404(db, session_id)
    rows = (
        await db.scalars(
            select(SimulationRun)
            .where(SimulationRun.session_id == session_id)
            .order_by(SimulationRun.created_at.desc())
        )
    ).all()
    return [_run_out(r) for r in rows]


@router.get("/runs/{run_id}", response_model=SimulationRunOut)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)) -> SimulationRunOut:
    run = await db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    traces = list(
        (
            await db.scalars(
                select(SimulationStepTrace)
                .where(SimulationStepTrace.run_id == run.id)
                .order_by(SimulationStepTrace.step_index.asc())
            )
        ).all()
    )
    return _run_out(run, traces)
