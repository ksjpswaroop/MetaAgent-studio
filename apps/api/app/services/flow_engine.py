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


_FALLBACK_SCENARIOS = [
    {
        "kind": "happy",
        "title": "Smooth day",
        "ascii_flow": "Check input → Do the work → Reply safely",
        "steps": [
            {
                "step_index": 0,
                "name": "Check input",
                "processing_goal": "Validate the request is complete",
                "expected_output": "Clean input",
            },
            {
                "step_index": 1,
                "name": "Do the work",
                "processing_goal": "Complete the main task",
                "expected_output": "Result ready",
            },
        ],
    },
    {
        "kind": "ambiguity",
        "title": "Missing pieces",
        "ascii_flow": "Check input → Ask what’s missing → Wait",
        "steps": [
            {
                "step_index": 0,
                "name": "Ask clarifying question",
                "processing_goal": "Fill gaps before acting",
                "expected_output": "Clarification request",
            }
        ],
    },
    {
        "kind": "failure",
        "title": "When things break",
        "ascii_flow": "Check input → Service busy → Queue & retry",
        "steps": [
            {
                "step_index": 0,
                "name": "Handle failure",
                "processing_goal": "Retry or escalate safely",
                "expected_output": "Queued retry",
            }
        ],
    },
]


def _normalize_scenarios(data: dict | None) -> list[dict]:
    raw = (data or {}).get("scenarios") or []
    out: list[dict] = []
    kinds = ("happy", "ambiguity", "failure")
    for i, scen in enumerate(raw):
        if not isinstance(scen, dict):
            continue
        kind = str(scen.get("kind") or kinds[min(i, 2)]).lower()
        if kind not in kinds:
            if "happy" in kind or "smooth" in kind:
                kind = "happy"
            elif "fail" in kind or "error" in kind or "break" in kind:
                kind = "failure"
            else:
                kind = "ambiguity"
        steps_in = scen.get("steps") or []
        steps: list[dict] = []
        for j, step in enumerate(steps_in):
            if not isinstance(step, dict):
                continue
            name = step.get("name") or step.get("title") or f"Step {j + 1}"
            steps.append(
                {
                    "step_index": int(step.get("step_index", j)),
                    "name": str(name),
                    "input_data": step.get("input_data") or {},
                    "processing_goal": str(
                        step.get("processing_goal") or step.get("goal") or ""
                    ),
                    "expected_output": str(step.get("expected_output") or ""),
                    "notes": str(step.get("notes") or ""),
                }
            )
        if not steps:
            steps = [
                {
                    "step_index": 0,
                    "name": "Main step",
                    "input_data": {},
                    "processing_goal": "Complete the task",
                    "expected_output": "Done",
                    "notes": "",
                }
            ]
        out.append(
            {
                "kind": kind,
                "title": str(scen.get("title") or kind),
                "ascii_flow": str(scen.get("ascii_flow") or ""),
                "mermaid_flow": str(scen.get("mermaid_flow") or ""),
                "steps": steps,
            }
        )
    if not out:
        return list(_FALLBACK_SCENARIOS)
    # Ensure happy/ambiguity/failure all present for the studio UI
    by_kind = {s["kind"]: s for s in out}
    for fb in _FALLBACK_SCENARIOS:
        by_kind.setdefault(fb["kind"], fb)
    return [by_kind["happy"], by_kind["ambiguity"], by_kind["failure"]]


async def generate_flows(db: AsyncSession, session: StudioSession) -> list[ExecutionScenario]:
    scope = await db.scalar(
        select(ScopeEnvelopeRow).where(ScopeEnvelopeRow.session_id == session.id)
    )
    scope_payload = json.loads(scope.raw_json) if scope else {"project_name": "Project"}
    try:
        data = await chat_json(
            db,
            task="flows_generate",
            system=(
                "You are WorkflowDesignerAgent. Return ONLY JSON with key scenarios: "
                "array of {kind: happy|ambiguity|failure, title, ascii_flow, steps:[{step_index,name,processing_goal}]}."
            ),
            user=json.dumps(scope_payload),
        )
    except Exception:
        data = {"scenarios": _FALLBACK_SCENARIOS}
    scenarios = _normalize_scenarios(data if isinstance(data, dict) else None)
    existing = (
        await db.scalars(
            select(ExecutionScenario).where(ExecutionScenario.session_id == session.id)
        )
    ).all()
    for s in existing:
        await db.delete(s)
    await db.flush()

    created: list[ExecutionScenario] = []
    for idx, scen in enumerate(scenarios):
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
