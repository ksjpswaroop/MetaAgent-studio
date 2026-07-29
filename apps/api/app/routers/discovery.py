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
from app.services import discovery_engine
from app.services.session_helpers import append_event, get_session_or_404
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
    created = await discovery_engine.start_discovery(db, session)
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
        db, session_id, "discovery.answered", {"question_key": body.question_key}
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
    body: ScopeFinalizeRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ScopeEnvelope:
    session = await get_session_or_404(db, session_id)
    override = body.scope.model_dump() if body and body.scope else None
    if override and override.get("trigger_type") not in {"webhook", "cron", "manual"}:
        raise HTTPException(status_code=422, detail="Invalid trigger_type")
    scope = await discovery_engine.finalize_from_transcript(db, session, override)
    await db.commit()
    return ScopeEnvelope(**scope)


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
