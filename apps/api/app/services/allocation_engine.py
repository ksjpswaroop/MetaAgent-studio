from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExecutionScenario, ScenarioStep, StepAllocation, StudioSession
from app.services.llm.client import chat_json
from app.services.session_helpers import append_event, load_state, save_state
from app.utils.ids import new_id
from app.utils.time import utc_now


async def run_allocation(db: AsyncSession, session: StudioSession) -> list[StepAllocation]:
    scenarios = (
        await db.scalars(
            select(ExecutionScenario).where(
                ExecutionScenario.session_id == session.id,
                ExecutionScenario.kind == "happy",
            )
        )
    ).all()
    steps: list[dict] = []
    if scenarios:
        scen_steps = (
            await db.scalars(
                select(ScenarioStep)
                .where(ScenarioStep.scenario_id == scenarios[0].id)
                .order_by(ScenarioStep.step_index.asc())
            )
        ).all()
        steps = [
            {"step_index": s.step_index, "name": s.name, "goal": s.processing_goal}
            for s in scen_steps
        ]
    data = await chat_json(
        db,
        task="allocation_run",
        system="You are IntelligenceAllocatorAgent. Assign Tier 1/2/3 per step as JSON.",
        user=json.dumps({"steps": steps}),
    )
    existing = (
        await db.scalars(
            select(StepAllocation).where(StepAllocation.session_id == session.id)
        )
    ).all()
    for row in existing:
        await db.delete(row)
    await db.flush()

    created: list[StepAllocation] = []
    for item in data.get("allocations", []):
        row = StepAllocation(
            id=new_id("alloc"),
            session_id=session.id,
            step_id=int(item["step_id"]),
            step_name=item["step_name"],
            description=item.get("description", ""),
            allocated_tier=item["allocated_tier"],
            rationale=item.get("rationale", ""),
            suggested_tech=item.get("suggested_tech", ""),
            user_override=False,
            updated_at=utc_now(),
        )
        db.add(row)
        created.append(row)
    session.stage = "allocated"
    state = load_state(session)
    state["allocations"] = data.get("allocations", [])
    save_state(session, state)
    await append_event(db, session.id, "allocation.completed")
    return created
