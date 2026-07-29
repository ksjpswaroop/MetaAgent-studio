from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DiscoveryMessage, ScopeEnvelopeRow
from app.db.session import get_db
from app.models.schemas import (
    DiscoveryAnswerRequest,
    DiscoveryMessageOut,
    ScopeEnvelope,
    ScopeFinalizeRequest,
)
from app.services.session_helpers import (
    append_event,
    get_session_or_404,
    load_state,
    save_state,
)
from app.stubs.sample_data import DISCOVERY_QUESTIONS
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


def _msg_out(m: DiscoveryMessage) -> DiscoveryMessageOut:
    return DiscoveryMessageOut(
        id=m.id,
        role=m.role,
        content=m.content,
        question_key=m.question_key,
        created_at=m.created_at,
    )


@router.post("/{session_id}/start", response_model=list[DiscoveryMessageOut])
async def start_discovery(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[DiscoveryMessageOut]:
    session = await get_session_or_404(db, session_id)
    session.stage = "discovery"
    session.updated_at = utc_now()
    created: list[DiscoveryMessage] = []
    intro = DiscoveryMessage(
        id=new_id("dmsg"),
        session_id=session_id,
        role="assistant",
        content="Let's clarify scope with a few questions.",
        question_key=None,
        created_at=utc_now(),
    )
    db.add(intro)
    created.append(intro)
    for q in DISCOVERY_QUESTIONS:
        msg = DiscoveryMessage(
            id=new_id("dmsg"),
            session_id=session_id,
            role="assistant",
            content=q["content"],
            question_key=q["question_key"],
            created_at=utc_now(),
        )
        db.add(msg)
        created.append(msg)
    await append_event(db, session_id, "discovery.started")
    await db.commit()
    return [_msg_out(m) for m in created]


@router.post("/{session_id}/answer", response_model=DiscoveryMessageOut)
async def answer_discovery(
    session_id: str,
    body: DiscoveryAnswerRequest,
    db: AsyncSession = Depends(get_db),
) -> DiscoveryMessageOut:
    await get_session_or_404(db, session_id)
    msg = DiscoveryMessage(
        id=new_id("dmsg"),
        session_id=session_id,
        role="user",
        content=body.answer,
        question_key=body.question_key,
        created_at=utc_now(),
    )
    db.add(msg)
    await append_event(
        db,
        session_id,
        "discovery.answered",
        {"question_key": body.question_key},
    )
    await db.commit()
    await db.refresh(msg)
    return _msg_out(msg)


@router.get("/{session_id}/messages", response_model=list[DiscoveryMessageOut])
async def list_messages(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[DiscoveryMessageOut]:
    await get_session_or_404(db, session_id)
    rows = (
        await db.scalars(
            select(DiscoveryMessage)
            .where(DiscoveryMessage.session_id == session_id)
            .order_by(DiscoveryMessage.created_at.asc())
        )
    ).all()
    return [_msg_out(m) for m in rows]


@router.post("/{session_id}/finalize", response_model=ScopeEnvelope)
async def finalize_scope(
    session_id: str,
    body: ScopeFinalizeRequest,
    db: AsyncSession = Depends(get_db),
) -> ScopeEnvelope:
    session = await get_session_or_404(db, session_id)
    scope = body.scope
    if scope.trigger_type not in {"webhook", "cron", "manual"}:
        raise HTTPException(status_code=422, detail="Invalid trigger_type")
    existing = await db.scalar(
        select(ScopeEnvelopeRow).where(ScopeEnvelopeRow.session_id == session_id)
    )
    raw = scope.model_dump()
    if existing:
        existing.project_name = scope.project_name
        existing.primary_goal = scope.primary_goal
        existing.trigger_type = scope.trigger_type
        existing.external_tools_json = json.dumps(scope.external_tools)
        existing.human_in_loop = scope.human_in_loop
        existing.fallback_strategy = scope.fallback_strategy
        existing.raw_json = json.dumps(raw)
    else:
        db.add(
            ScopeEnvelopeRow(
                id=new_id("scope"),
                session_id=session_id,
                project_name=scope.project_name,
                primary_goal=scope.primary_goal,
                trigger_type=scope.trigger_type,
                external_tools_json=json.dumps(scope.external_tools),
                human_in_loop=scope.human_in_loop,
                fallback_strategy=scope.fallback_strategy,
                raw_json=json.dumps(raw),
                created_at=utc_now(),
            )
        )
    state = load_state(session)
    state["scope_envelope"] = raw
    save_state(session, state)
    session.stage = "scope_ready"
    await append_event(db, session_id, "discovery.finalized", raw)
    await db.commit()
    return scope


@router.get("/{session_id}/scope", response_model=ScopeEnvelope)
async def get_scope(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> ScopeEnvelope:
    await get_session_or_404(db, session_id)
    row = await db.scalar(
        select(ScopeEnvelopeRow).where(ScopeEnvelopeRow.session_id == session_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Scope not finalized")
    return ScopeEnvelope(
        project_name=row.project_name,
        primary_goal=row.primary_goal,
        trigger_type=row.trigger_type,
        external_tools=json.loads(row.external_tools_json or "[]"),
        human_in_loop=bool(row.human_in_loop),
        fallback_strategy=row.fallback_strategy,
    )
