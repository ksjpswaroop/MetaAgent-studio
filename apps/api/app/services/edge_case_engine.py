from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    EdgeCase,
    ExecutionScenario,
    ScenarioStep,
    StudioSession,
)
from app.services.llm.client import chat_json
from app.services.session_helpers import append_event
from app.utils.ids import new_id
from app.utils.time import utc_now


async def generate_edge_cases(
    db: AsyncSession, session: StudioSession, count: int = 5
) -> list[EdgeCase]:
    data = await chat_json(
        db,
        task="edge_cases",
        system="Generate edge cases for multi-agent workflow as JSON.",
        user=json.dumps({"session_id": session.id, "count": count}),
    )
    created: list[EdgeCase] = []
    for item in (data.get("edge_cases") or [])[:count]:
        row = EdgeCase(
            id=new_id("edge"),
            session_id=session.id,
            agent_name=item.get("agent_name"),
            step_name=item.get("step_name"),
            category=item.get("category", "other"),
            title=item.get("title", "Edge case"),
            description=item.get("description", ""),
            input_fixture_json=json.dumps(item.get("input_fixture") or {}),
            expected_behavior=item.get("expected_behavior", ""),
            attached_scenario_id=None,
            created_at=utc_now(),
        )
        db.add(row)
        created.append(row)
    await append_event(db, session.id, "edge_cases.generated", {"count": len(created)})
    return created


async def attach_edge_case(
    db: AsyncSession, session: StudioSession, case: EdgeCase
) -> EdgeCase:
    failure = await db.scalar(
        select(ExecutionScenario).where(
            ExecutionScenario.session_id == session.id,
            ExecutionScenario.kind == "failure",
        )
    )
    if failure is None:
        failure = ExecutionScenario(
            id=new_id("scen"),
            session_id=session.id,
            kind="failure",
            title="Generated Edge Cases",
            ascii_flow="Edge",
            mermaid_flow="",
            sort_order=99,
            is_approved=False,
            created_at=utc_now(),
        )
        db.add(failure)
        await db.flush()
    steps = (
        await db.scalars(
            select(ScenarioStep).where(ScenarioStep.scenario_id == failure.id)
        )
    ).all()
    next_idx = max((s.step_index for s in steps), default=0) + 1
    db.add(
        ScenarioStep(
            id=new_id("step"),
            scenario_id=failure.id,
            step_index=next_idx,
            name=case.title,
            input_data_json=case.input_fixture_json,
            processing_goal=case.description,
            expected_output=case.expected_behavior,
            notes=f"edge_case:{case.id}",
        )
    )
    case.attached_scenario_id = failure.id
    await append_event(db, session.id, "edge_cases.attached", {"case_id": case.id})
    return case
