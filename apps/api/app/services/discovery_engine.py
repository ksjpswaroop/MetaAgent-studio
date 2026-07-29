from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DiscoveryMessage, ScopeEnvelopeRow, StudioSession
from app.services.llm.client import chat_json
from app.services.session_helpers import append_event, load_state, save_state
from app.utils.ids import new_id
from app.utils.time import utc_now


async def start_discovery(db: AsyncSession, session: StudioSession) -> list[DiscoveryMessage]:
    data = await chat_json(
        db,
        task="discovery_questions",
        system="You are RequirementsArchitectAgent. Return JSON with questions array.",
        user=session.raw_user_prompt,
    )
    session.stage = "discovery"
    session.updated_at = utc_now()
    created: list[DiscoveryMessage] = []
    intro = DiscoveryMessage(
        id=new_id("dmsg"),
        session_id=session.id,
        role="assistant",
        content="Let's clarify scope with a few questions.",
        question_key=None,
        created_at=utc_now(),
    )
    db.add(intro)
    created.append(intro)
    for q in data.get("questions", []):
        msg = DiscoveryMessage(
            id=new_id("dmsg"),
            session_id=session.id,
            role="assistant",
            content=q.get("content", ""),
            question_key=q.get("question_key"),
            created_at=utc_now(),
        )
        db.add(msg)
        created.append(msg)
    await append_event(db, session.id, "discovery.started")
    return created


async def finalize_from_transcript(
    db: AsyncSession, session: StudioSession, override: dict | None = None
) -> dict:
    if override:
        scope = override
    else:
        rows = (
            await db.scalars(
                select(DiscoveryMessage)
                .where(DiscoveryMessage.session_id == session.id)
                .order_by(DiscoveryMessage.created_at.asc())
            )
        ).all()
        transcript = [
            {"role": r.role, "question_key": r.question_key, "content": r.content}
            for r in rows
        ]
        scope = await chat_json(
            db,
            task="discovery_finalize",
            system="Synthesize a ScopeEnvelope JSON from the Q&A transcript.",
            user=json.dumps(
                {"prompt": session.raw_user_prompt, "transcript": transcript}
            ),
        )

    existing = await db.scalar(
        select(ScopeEnvelopeRow).where(ScopeEnvelopeRow.session_id == session.id)
    )
    tools = scope.get("external_tools") or []
    if existing:
        existing.project_name = scope["project_name"]
        existing.primary_goal = scope["primary_goal"]
        existing.trigger_type = scope["trigger_type"]
        existing.external_tools_json = json.dumps(tools)
        existing.human_in_loop = bool(scope.get("human_in_loop"))
        existing.fallback_strategy = scope.get("fallback_strategy") or ""
        existing.raw_json = json.dumps(scope)
    else:
        db.add(
            ScopeEnvelopeRow(
                id=new_id("scope"),
                session_id=session.id,
                project_name=scope["project_name"],
                primary_goal=scope["primary_goal"],
                trigger_type=scope["trigger_type"],
                external_tools_json=json.dumps(tools),
                human_in_loop=bool(scope.get("human_in_loop")),
                fallback_strategy=scope.get("fallback_strategy") or "",
                raw_json=json.dumps(scope),
                created_at=utc_now(),
            )
        )
    state = load_state(session)
    state["scope_envelope"] = scope
    save_state(session, state)
    session.stage = "scope_ready"
    await append_event(db, session.id, "discovery.finalized", scope)
    return scope
