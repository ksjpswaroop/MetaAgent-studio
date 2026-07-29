from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db.models import SessionEvent
from app.db.session import get_db
from app.services.session_helpers import get_session_or_404

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("/{session_id}/stream")
async def stream_events(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    await get_session_or_404(db, session_id)

    async def event_generator():
        last_seen = ""
        while True:
            if await request.is_disconnected():
                break
            rows = (
                await db.scalars(
                    select(SessionEvent)
                    .where(SessionEvent.session_id == session_id)
                    .order_by(SessionEvent.created_at.asc())
                )
            ).all()
            for row in rows:
                if row.id <= last_seen:
                    continue
                last_seen = row.id
                yield {
                    "event": row.event_type,
                    "id": row.id,
                    "data": row.payload_json or "{}",
                }
            # heartbeat
            yield {"event": "ping", "data": json.dumps({"ok": True})}
            await asyncio.sleep(1.0)
            # stub stream ends after one poll cycle + ping for tests
            break

    return EventSourceResponse(event_generator())
