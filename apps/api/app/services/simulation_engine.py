from __future__ import annotations

import json
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    EdgeCase,
    ExecutionScenario,
    SimulationRun,
    SimulationStepTrace,
    StudioSession,
)
from app.services.session_helpers import append_event
from app.utils.ids import new_id
from app.utils.time import utc_now


def _score(traces: list[SimulationStepTrace], allocations_count: int) -> dict:
    if not traces:
        return {
            "overall": 0.0,
            "correctness": 0.0,
            "gate_pass_rate": 0.0,
            "latency_budget": 0.0,
            "tier_efficiency": 0.0,
        }
    passed = sum(1 for t in traces if t.passed)
    correctness = passed / len(traces)
    gate_pass = correctness
    avg_latency = sum(t.latency_ms or 0 for t in traces) / len(traces)
    latency_budget = 1.0 if avg_latency < 500 else max(0.0, 1.0 - (avg_latency - 500) / 2000)
    tier_efficiency = 0.75 if allocations_count else 0.5
    overall = round(
        0.4 * correctness + 0.3 * gate_pass + 0.15 * latency_budget + 0.15 * tier_efficiency,
        4,
    )
    return {
        "overall": overall,
        "correctness": round(correctness, 4),
        "gate_pass_rate": round(gate_pass, 4),
        "latency_budget": round(latency_budget, 4),
        "tier_efficiency": round(tier_efficiency, 4),
    }


async def run_simulation(
    db: AsyncSession,
    session: StudioSession,
    *,
    scenario_ids: list[str] | None = None,
    edge_case_ids: list[str] | None = None,
    include_all_scenarios: bool = True,
) -> SimulationRun:
    q = select(ExecutionScenario).where(ExecutionScenario.session_id == session.id)
    if scenario_ids:
        q = q.where(ExecutionScenario.id.in_(scenario_ids))
    elif not include_all_scenarios:
        q = q.where(ExecutionScenario.kind == "happy")
    scenarios = list(
        (
            await db.scalars(
                q.options(selectinload(ExecutionScenario.steps)).order_by(
                    ExecutionScenario.sort_order.asc()
                )
            )
        ).all()
    )
    edge_ids = edge_case_ids or []
    edges: list[EdgeCase] = []
    if edge_ids:
        edges = list(
            (
                await db.scalars(select(EdgeCase).where(EdgeCase.id.in_(edge_ids)))
            ).all()
        )

    run = SimulationRun(
        id=new_id("sim"),
        session_id=session.id,
        status="running",
        scenario_ids_json=json.dumps([s.id for s in scenarios]),
        edge_case_ids_json=json.dumps(edge_ids),
        score_json="{}",
        summary="",
        started_at=utc_now(),
        finished_at=None,
        created_at=utc_now(),
    )
    db.add(run)
    await db.flush()

    traces: list[SimulationStepTrace] = []
    step_i = 0
    for scen in scenarios:
        for st in sorted(scen.steps, key=lambda x: x.step_index):
            started = time.perf_counter()
            fixture = json.loads(st.input_data_json or "{}")
            # Deterministic sim: fail on known edge markers
            fail = bool(
                fixture.get("force_timeout")
                or fixture.get("emit_fail")
                or "timeout" in (st.notes or "").lower()
                or scen.kind == "failure"
                and "Fallback" in st.name
            )
            # Happy path steps pass; ambiguity clarify passes; injected failures fail
            if scen.kind == "happy":
                passed = True
            elif scen.kind == "ambiguity":
                passed = True
            else:
                passed = not fail and "fail" not in st.name.lower()
                if "Fallback" in st.name or fixture.get("error"):
                    passed = False
            latency = int((time.perf_counter() - started) * 1000) + 5
            tr = SimulationStepTrace(
                id=new_id("strace"),
                run_id=run.id,
                step_index=step_i,
                step_name=st.name,
                agent_name=None,
                input_json=st.input_data_json or "{}",
                output_json=json.dumps(
                    {"ok": passed, "scenario": scen.kind, "expected": st.expected_output}
                ),
                passed=passed,
                latency_ms=latency,
                error=None if passed else f"Simulated failure in {st.name}",
                created_at=utc_now(),
            )
            db.add(tr)
            traces.append(tr)
            step_i += 1

    for edge in edges:
        started = time.perf_counter()
        fixture = json.loads(edge.input_fixture_json or "{}")
        passed = False  # edge cases are expected stress; mark fail to drive improvement
        tr = SimulationStepTrace(
            id=new_id("strace"),
            run_id=run.id,
            step_index=step_i,
            step_name=edge.title,
            agent_name=edge.agent_name,
            input_json=edge.input_fixture_json,
            output_json=json.dumps({"ok": False, "edge_case": edge.category}),
            passed=passed,
            latency_ms=int((time.perf_counter() - started) * 1000) + 8,
            error=f"Edge case: {edge.category}",
            created_at=utc_now(),
        )
        db.add(tr)
        traces.append(tr)
        step_i += 1

    score = _score(traces, allocations_count=1)
    run.score_json = json.dumps(score)
    run.finished_at = utc_now()
    if all(t.passed for t in traces):
        run.status = "passed"
    elif any(t.passed for t in traces):
        run.status = "partial"
    else:
        run.status = "failed"
    run.summary = (
        f"{sum(1 for t in traces if t.passed)}/{len(traces)} steps passed; "
        f"overall={score['overall']}"
    )
    await append_event(
        db,
        session.id,
        "simulation.completed",
        {"run_id": run.id, "status": run.status, "score": score},
    )
    return run
