from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ExecutionScenario, FlowRevisionLog, ScenarioStep, ScopeEnvelopeRow
from app.db.session import get_db
from app.models.schemas import ExecutionScenarioOut, FlowModifyRequest, ScenarioStepOut
from app.services.session_helpers import (
    append_event,
    get_session_or_404,
    load_state,
    require_stage,
    save_state,
)
from app.stubs.sample_data import stub_scenarios
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/flows", tags=["flows"])


def _scenario_out(s: ExecutionScenario) -> ExecutionScenarioOut:
    steps = sorted(s.steps, key=lambda x: x.step_index)
    return ExecutionScenarioOut(
        id=s.id,
        kind=s.kind,
        title=s.title,
        ascii_flow=s.ascii_flow,
        mermaid_flow=s.mermaid_flow,
        sort_order=s.sort_order,
        is_approved=bool(s.is_approved),
        steps=[
            ScenarioStepOut(
                step_index=st.step_index,
                name=st.name,
                input_data=json.loads(st.input_data_json or "{}"),
                processing_goal=st.processing_goal,
                expected_output=st.expected_output,
                notes=st.notes,
            )
            for st in steps
        ],
    )


async def _load_scenarios(db: AsyncSession, session_id: str) -> list[ExecutionScenario]:
    return list(
        (
            await db.scalars(
                select(ExecutionScenario)
                .where(ExecutionScenario.session_id == session_id)
                .options(selectinload(ExecutionScenario.steps))
                .order_by(ExecutionScenario.sort_order.asc())
            )
        ).all()
    )


@router.post("/{session_id}/generate", response_model=list[ExecutionScenarioOut])
async def generate_flows(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ExecutionScenarioOut]:
    session = await get_session_or_404(db, session_id)
    require_stage(
        session,
        {"scope_ready", "flows", "flow_approved", "allocated", "architected", "gated", "scaffolded"},
        "Scope must be finalized before generating flows",
    )
    scope = await db.scalar(
        select(ScopeEnvelopeRow).where(ScopeEnvelopeRow.session_id == session_id)
    )
    project_name = scope.project_name if scope else "Project"

    # Replace existing stub scenarios
    existing = await _load_scenarios(db, session_id)
    for s in existing:
        await db.delete(s)
    await db.flush()

    created: list[ExecutionScenario] = []
    for data in stub_scenarios(project_name):
        scenario = ExecutionScenario(
            id=new_id("scen"),
            session_id=session_id,
            kind=data["kind"],
            title=data["title"],
            ascii_flow=data["ascii_flow"],
            mermaid_flow=data["mermaid_flow"],
            sort_order=data["sort_order"],
            is_approved=False,
            created_at=utc_now(),
        )
        db.add(scenario)
        await db.flush()
        for step in data["steps"]:
            db.add(
                ScenarioStep(
                    id=new_id("step"),
                    scenario_id=scenario.id,
                    step_index=step["step_index"],
                    name=step["name"],
                    input_data_json=json.dumps(step.get("input_data", {})),
                    processing_goal=step.get("processing_goal", ""),
                    expected_output=step.get("expected_output", ""),
                    notes=step.get("notes", ""),
                )
            )
        created.append(scenario)

    session.stage = "flows"
    state = load_state(session)
    state["sample_flows"] = [
        {"kind": c.kind, "title": c.title} for c in created
    ]
    save_state(session, state)
    await append_event(db, session_id, "flows.generated")
    await db.commit()
    scenarios = await _load_scenarios(db, session_id)
    return [_scenario_out(s) for s in scenarios]


@router.get("/{session_id}", response_model=list[ExecutionScenarioOut])
async def get_flows(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ExecutionScenarioOut]:
    await get_session_or_404(db, session_id)
    scenarios = await _load_scenarios(db, session_id)
    return [_scenario_out(s) for s in scenarios]


@router.post("/{session_id}/modify", response_model=list[ExecutionScenarioOut])
async def modify_flow(
    session_id: str,
    body: FlowModifyRequest,
    db: AsyncSession = Depends(get_db),
) -> list[ExecutionScenarioOut]:
    await get_session_or_404(db, session_id)
    scenarios = await _load_scenarios(db, session_id)
    if not scenarios:
        raise HTTPException(status_code=404, detail="No scenarios to modify")
    target = scenarios[0]
    before = _scenario_out(target).model_dump()
    for st in target.steps:
        if st.step_index == body.step_index:
            if "name" in body.changes:
                st.name = str(body.changes["name"])
            if "processing_goal" in body.changes:
                st.processing_goal = str(body.changes["processing_goal"])
            if "notes" in body.changes:
                st.notes = str(body.changes["notes"])
            break
    db.add(
        FlowRevisionLog(
            id=new_id("frev"),
            session_id=session_id,
            action="modify",
            before_json=json.dumps(before),
            after_json=json.dumps(body.changes),
            note=body.note,
            created_at=utc_now(),
        )
    )
    await append_event(db, session_id, "flows.modified", {"step_index": body.step_index})
    await db.commit()
    return [_scenario_out(s) for s in await _load_scenarios(db, session_id)]


@router.post("/{session_id}/add-fallback", response_model=list[ExecutionScenarioOut])
async def add_fallback(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ExecutionScenarioOut]:
    await get_session_or_404(db, session_id)
    scenarios = await _load_scenarios(db, session_id)
    if not scenarios:
        raise HTTPException(status_code=404, detail="No scenarios")
    failure = next((s for s in scenarios if s.kind == "failure"), scenarios[-1])
    next_idx = max((st.step_index for st in failure.steps), default=0) + 1
    db.add(
        ScenarioStep(
            id=new_id("step"),
            scenario_id=failure.id,
            step_index=next_idx,
            name="Additional Fallback Node",
            input_data_json="{}",
            processing_goal="Handle unexpected failure mode",
            expected_output="Safe degraded response",
            notes="Added via add-fallback",
        )
    )
    db.add(
        FlowRevisionLog(
            id=new_id("frev"),
            session_id=session_id,
            action="add_fallback",
            before_json="{}",
            after_json=json.dumps({"step_index": next_idx}),
            note="",
            created_at=utc_now(),
        )
    )
    await append_event(db, session_id, "flows.add_fallback")
    await db.commit()
    return [_scenario_out(s) for s in await _load_scenarios(db, session_id)]


@router.post("/{session_id}/re-route", response_model=list[ExecutionScenarioOut])
async def re_route(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ExecutionScenarioOut]:
    await get_session_or_404(db, session_id)
    scenarios = await _load_scenarios(db, session_id)
    for s in scenarios:
        s.mermaid_flow = (s.mermaid_flow or "") + "\n  %% re-routed"
        s.ascii_flow = (s.ascii_flow or "") + "\n  [re-routed]"
    db.add(
        FlowRevisionLog(
            id=new_id("frev"),
            session_id=session_id,
            action="re_route",
            before_json="{}",
            after_json="{}",
            note="re-route",
            created_at=utc_now(),
        )
    )
    await append_event(db, session_id, "flows.re_routed")
    await db.commit()
    return [_scenario_out(s) for s in await _load_scenarios(db, session_id)]


@router.post("/{session_id}/approve", response_model=list[ExecutionScenarioOut])
async def approve_flow(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ExecutionScenarioOut]:
    session = await get_session_or_404(db, session_id)
    scenarios = await _load_scenarios(db, session_id)
    if not scenarios:
        raise HTTPException(status_code=404, detail="No scenarios to approve")
    for s in scenarios:
        s.is_approved = True
    session.flow_approved = True
    session.stage = "flow_approved"
    state = load_state(session)
    state["flow_approved"] = True
    save_state(session, state)
    db.add(
        FlowRevisionLog(
            id=new_id("frev"),
            session_id=session_id,
            action="accept",
            before_json="{}",
            after_json='{"approved": true}',
            note="",
            created_at=utc_now(),
        )
    )
    await append_event(db, session_id, "flows.approved")
    await db.commit()
    return [_scenario_out(s) for s in await _load_scenarios(db, session_id)]
