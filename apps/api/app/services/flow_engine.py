from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ExecutionScenario, ScenarioStep, ScopeEnvelopeRow, StudioSession
from app.services.llm.client import chat_json
from app.services.session_helpers import append_event, load_state, save_state
from app.utils.ids import new_id
from app.utils.time import utc_now


async def generate_flows(db: AsyncSession, session: StudioSession) -> list[ExecutionScenario]:
    scope = await db.scalar(
        select(ScopeEnvelopeRow).where(ScopeEnvelopeRow.session_id == session.id)
    )
    scope_payload = json.loads(scope.raw_json) if scope else {"project_name": "Project"}
    data = await chat_json(
        db,
        task="flows_generate",
        system="You are WorkflowDesignerAgent. Return JSON scenarios happy/ambiguity/failure.",
        user=json.dumps(scope_payload),
    )
    existing = (
        await db.scalars(
            select(ExecutionScenario).where(ExecutionScenario.session_id == session.id)
        )
    ).all()
    for s in existing:
        await db.delete(s)
    await db.flush()

    created: list[ExecutionScenario] = []
    for idx, scen in enumerate(data.get("scenarios", [])):
        row = ExecutionScenario(
            id=new_id("scen"),
            session_id=session.id,
            kind=scen["kind"],
            title=scen.get("title", scen["kind"]),
            ascii_flow=scen.get("ascii_flow", ""),
            mermaid_flow=scen.get("mermaid_flow", ""),
            sort_order=idx,
            is_approved=False,
            created_at=utc_now(),
        )
        db.add(row)
        await db.flush()
        for step in scen.get("steps", []):
            db.add(
                ScenarioStep(
                    id=new_id("step"),
                    scenario_id=row.id,
                    step_index=int(step["step_index"]),
                    name=step["name"],
                    input_data_json=json.dumps(step.get("input_data") or {}),
                    processing_goal=step.get("processing_goal", ""),
                    expected_output=step.get("expected_output", ""),
                    notes=step.get("notes", ""),
                )
            )
        created.append(row)
    session.stage = "flows"
    state = load_state(session)
    state["sample_flows"] = [{"kind": c.kind, "title": c.title} for c in created]
    save_state(session, state)
    await append_event(db, session.id, "flows.generated")
    await db.flush()
    return list(
        (
            await db.scalars(
                select(ExecutionScenario)
                .where(ExecutionScenario.session_id == session.id)
                .options(selectinload(ExecutionScenario.steps))
                .order_by(ExecutionScenario.sort_order.asc())
            )
        ).all()
    )
