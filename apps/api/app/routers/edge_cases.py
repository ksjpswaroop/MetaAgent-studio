from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EdgeCase
from app.db.session import get_db
from app.models.schemas import EdgeCaseGenerateRequest, EdgeCaseOut
from app.services import edge_case_engine
from app.services.session_helpers import get_session_or_404

router = APIRouter(prefix="/api/v1/edge-cases", tags=["edge-cases"])


def _out(e: EdgeCase) -> EdgeCaseOut:
    return EdgeCaseOut(
        id=e.id,
        session_id=e.session_id,
        agent_name=e.agent_name,
        step_name=e.step_name,
        category=e.category,
        title=e.title,
        description=e.description,
        input_fixture=json.loads(e.input_fixture_json or "{}"),
        expected_behavior=e.expected_behavior,
        attached_scenario_id=e.attached_scenario_id,
        created_at=e.created_at,
    )


@router.post("/{session_id}/generate", response_model=list[EdgeCaseOut])
async def generate(
    session_id: str,
    body: EdgeCaseGenerateRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[EdgeCaseOut]:
    body = body or EdgeCaseGenerateRequest()
    session = await get_session_or_404(db, session_id)
    rows = await edge_case_engine.generate_edge_cases(db, session, count=body.count)
    await db.commit()
    return [_out(r) for r in rows]


@router.get("/{session_id}", response_model=list[EdgeCaseOut])
async def list_cases(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[EdgeCaseOut]:
    await get_session_or_404(db, session_id)
    rows = (
        await db.scalars(
            select(EdgeCase)
            .where(EdgeCase.session_id == session_id)
            .order_by(EdgeCase.created_at.desc())
        )
    ).all()
    return [_out(r) for r in rows]


@router.post("/{session_id}/{case_id}/attach-to-flows", response_model=EdgeCaseOut)
async def attach(
    session_id: str, case_id: str, db: AsyncSession = Depends(get_db)
) -> EdgeCaseOut:
    session = await get_session_or_404(db, session_id)
    case = await db.get(EdgeCase, case_id)
    if case is None or case.session_id != session_id:
        raise HTTPException(status_code=404, detail="Edge case not found")
    await edge_case_engine.attach_edge_case(db, session, case)
    await db.commit()
    await db.refresh(case)
    return _out(case)
