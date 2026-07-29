from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SessionEvent, StudioSession
from app.utils.ids import new_id
from app.utils.time import utc_now


async def get_session_or_404(db: AsyncSession, session_id: str) -> StudioSession:
    session = await db.get(StudioSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def append_event(
    db: AsyncSession,
    session_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> SessionEvent:
    event = SessionEvent(
        id=new_id("evt"),
        session_id=session_id,
        event_type=event_type,
        payload_json=json.dumps(payload or {}),
        created_at=utc_now(),
    )
    db.add(event)
    return event


def load_state(session: StudioSession) -> dict[str, Any]:
    try:
        return json.loads(session.state_json or "{}")
    except json.JSONDecodeError:
        return {}


def save_state(session: StudioSession, state: dict[str, Any]) -> None:
    session.state_json = json.dumps(state)
    session.updated_at = utc_now()


def require_stage(session: StudioSession, allowed: set[str], message: str) -> None:
    if session.stage not in allowed and not (
        session.flow_approved and "flow_approved" in allowed
    ):
        # Allow later stages that imply prerequisites
        order = [
            "created",
            "discovery",
            "scope_ready",
            "flows",
            "flow_approved",
            "allocated",
            "architected",
            "gated",
            "scaffolded",
        ]
        min_allowed = min(order.index(s) for s in allowed if s in order)
        current = order.index(session.stage) if session.stage in order else -1
        if current >= min_allowed:
            return
        raise HTTPException(status_code=409, detail=message)
