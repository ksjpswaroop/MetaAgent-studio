from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CodingGapPrompt
from app.db.session import get_db
from app.models.schemas import CodingGapPromptOut, PromptGenerateRequest
from app.services import prompt_engine
from app.services.session_helpers import get_session_or_404

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


def _out(p: CodingGapPrompt) -> CodingGapPromptOut:
    return CodingGapPromptOut(
        id=p.id,
        session_id=p.session_id,
        simulation_run_id=p.simulation_run_id,
        tool_target=p.tool_target,
        title=p.title,
        gap_description=p.gap_description,
        files=json.loads(p.files_json or "[]"),
        acceptance_criteria=p.acceptance_criteria,
        prompt_text=p.prompt_text,
        created_at=p.created_at,
    )


@router.post("/{session_id}/generate", response_model=list[CodingGapPromptOut])
async def generate(
    session_id: str,
    body: PromptGenerateRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[CodingGapPromptOut]:
    body = body or PromptGenerateRequest()
    session = await get_session_or_404(db, session_id)
    rows = await prompt_engine.generate_prompts(
        db,
        session,
        simulation_run_id=body.simulation_run_id,
        tool_target=body.tool_target,
    )
    await db.commit()
    return [_out(r) for r in rows]


@router.get("/{session_id}", response_model=list[CodingGapPromptOut])
async def list_prompts(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[CodingGapPromptOut]:
    await get_session_or_404(db, session_id)
    rows = (
        await db.scalars(
            select(CodingGapPrompt)
            .where(CodingGapPrompt.session_id == session_id)
            .order_by(CodingGapPrompt.created_at.desc())
        )
    ).all()
    return [_out(r) for r in rows]
