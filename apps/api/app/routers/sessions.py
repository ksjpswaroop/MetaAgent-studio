from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, SessionEvent, StudioSession
from app.db.session import get_db
from app.models.schemas import SessionCreate, SessionEventOut, StudioSessionOut
from app.services.session_helpers import append_event, load_state, save_state
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


def _to_out(s: StudioSession) -> StudioSessionOut:
    return StudioSessionOut(
        id=s.id,
        project_id=s.project_id,
        stage=s.stage,
        raw_user_prompt=s.raw_user_prompt,
        flow_approved=bool(s.flow_approved),
        state=load_state(s),
        token_usage=s.token_usage,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.get("", response_model=list[StudioSessionOut])
async def list_sessions(
    project_id: str | None = None, db: AsyncSession = Depends(get_db)
) -> list[StudioSessionOut]:
    stmt = select(StudioSession).order_by(StudioSession.created_at.desc())
    if project_id:
        stmt = stmt.where(StudioSession.project_id == project_id)
    rows = (await db.scalars(stmt)).all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=StudioSessionOut, status_code=201)
async def create_session(
    body: SessionCreate, db: AsyncSession = Depends(get_db)
) -> StudioSessionOut:
    project = await db.get(Project, body.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    now = utc_now()
    session = StudioSession(
        id=new_id("sess"),
        project_id=body.project_id,
        stage="created",
        raw_user_prompt=body.raw_user_prompt,
        flow_approved=False,
        state_json=json.dumps(
            {
                "session_id": None,
                "raw_user_prompt": body.raw_user_prompt,
                "scope_envelope": None,
                "sample_flows": [],
                "flow_approved": False,
                "allocations": [],
                "agent_specs": [],
                "tool_specs": [],
                "generated_files": {},
            }
        ),
        token_usage=0,
        created_at=now,
        updated_at=now,
    )
    # Fix session_id inside state after id assigned
    state = json.loads(session.state_json)
    state["session_id"] = session.id
    session.state_json = json.dumps(state)
    db.add(session)
    await db.flush()
    await append_event(db, session.id, "session.created", {"project_id": project.id})
    await db.commit()
    await db.refresh(session)
    return _to_out(session)


@router.get("/{session_id}", response_model=StudioSessionOut)
async def get_session(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> StudioSessionOut:
    session = await db.get(StudioSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_out(session)


@router.patch("/{session_id}", response_model=StudioSessionOut)
async def patch_session(
    session_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> StudioSessionOut:
    session = await db.get(StudioSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    state = load_state(session)
    state.update(body)
    save_state(session, state)
    await db.commit()
    await db.refresh(session)
    return _to_out(session)


@router.get("/{session_id}/events", response_model=list[SessionEventOut])
async def list_events(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[SessionEventOut]:
    session = await db.get(StudioSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    rows = (
        await db.scalars(
            select(SessionEvent)
            .where(SessionEvent.session_id == session_id)
            .order_by(SessionEvent.created_at.asc())
        )
    ).all()
    out: list[SessionEventOut] = []
    for r in rows:
        try:
            payload = json.loads(r.payload_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        out.append(
            SessionEventOut(
                id=r.id,
                session_id=r.session_id,
                event_type=r.event_type,
                payload=payload,
                created_at=r.created_at,
            )
        )
    return out
