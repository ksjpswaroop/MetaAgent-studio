from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CodingGapPrompt, SimulationRun, SimulationStepTrace, StudioSession
from app.services.llm.client import chat_json
from app.services.session_helpers import append_event
from app.utils.ids import new_id
from app.utils.time import utc_now


async def generate_prompts(
    db: AsyncSession,
    session: StudioSession,
    *,
    simulation_run_id: str | None,
    tool_target: str = "cursor",
) -> list[CodingGapPrompt]:
    run_id = simulation_run_id
    if not run_id:
        latest = await db.scalar(
            select(SimulationRun)
            .where(SimulationRun.session_id == session.id)
            .order_by(SimulationRun.created_at.desc())
        )
        run_id = latest.id if latest else None
    failures: list[dict] = []
    if run_id:
        traces = (
            await db.scalars(
                select(SimulationStepTrace).where(
                    SimulationStepTrace.run_id == run_id,
                    SimulationStepTrace.passed.is_(False),
                )
            )
        ).all()
        failures = [
            {"step": t.step_name, "error": t.error, "input": json.loads(t.input_json or "{}")}
            for t in traces
        ]
    data = await chat_json(
        db,
        task="coding_gap_prompts",
        system=f"Generate coding-gap prompts for {tool_target} from simulation failures.",
        user=json.dumps({"failures": failures, "tool_target": tool_target}),
    )
    created: list[CodingGapPrompt] = []
    for item in data.get("prompts") or []:
        row = CodingGapPrompt(
            id=new_id("prompt"),
            session_id=session.id,
            simulation_run_id=run_id,
            tool_target=tool_target,
            title=item.get("title", "Coding gap"),
            gap_description=item.get("gap_description", ""),
            files_json=json.dumps(item.get("files") or []),
            acceptance_criteria=item.get("acceptance_criteria", ""),
            prompt_text=item.get("prompt_text", ""),
            created_at=utc_now(),
        )
        db.add(row)
        created.append(row)
    await append_event(
        db, session.id, "prompts.generated", {"count": len(created), "tool_target": tool_target}
    )
    return created
