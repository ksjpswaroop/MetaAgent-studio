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
    try:
        data = await chat_json(
            db,
            task="allocation_run",
            system=(
                "You are IntelligenceAllocatorAgent. Return JSON "
                '{"allocations":[{"step_id":0,"step_name":"...","allocated_tier":"TIER_1_CODE|TIER_2_CLASSICAL_ML|TIER_3_LLM_AGENT","rationale":"..."}]}'
            ),
            user=json.dumps({"steps": steps}),
        )
    except Exception:
        data = {}
    items = []
    if isinstance(data, dict):
        items = data.get("allocations") or []
    if not items:
        tiers = ["TIER_1_CODE", "TIER_2_CLASSICAL_ML", "TIER_3_LLM_AGENT"]
        items = [
            {
                "step_id": s.get("step_index", i),
                "step_name": s.get("name", f"Step {i}"),
                "description": s.get("goal", ""),
                "allocated_tier": tiers[i % 3],
                "rationale": "Default assignment for demo reliability",
                "suggested_tech": "",
            }
            for i, s in enumerate(steps or [{"step_index": 0, "name": "Main", "goal": ""}])
        ]
    existing = (
        await db.scalars(
            select(StepAllocation).where(StepAllocation.session_id == session.id)
        )
    ).all()
    for row in existing:
        await db.delete(row)
    await db.flush()

    created: list[StepAllocation] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        tier = str(item.get("allocated_tier") or "TIER_1_CODE")
        if tier not in {
            "TIER_1_CODE",
            "TIER_2_CLASSICAL_ML",
            "TIER_3_LLM_AGENT",
        }:
            tier = "TIER_3_LLM_AGENT"
        row = StepAllocation(
            id=new_id("alloc"),
            session_id=session.id,
            step_id=int(item.get("step_id", 0)),
            step_name=str(item.get("step_name") or "Step"),
            description=str(item.get("description") or ""),
            allocated_tier=tier,
            rationale=str(item.get("rationale") or ""),
            suggested_tech=str(item.get("suggested_tech") or ""),
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
