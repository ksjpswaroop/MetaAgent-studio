from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import StepAllocation
from app.db.session import get_db
from app.models.schemas import AllocationOverride, StepAllocationOut, TierType
from app.services.session_helpers import (
    append_event,
    get_session_or_404,
    load_state,
    save_state,
)
from app.stubs.sample_data import stub_allocations
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/allocation", tags=["allocation"])


def _out(row: StepAllocation) -> StepAllocationOut:
    return StepAllocationOut(
        step_id=row.step_id,
        step_name=row.step_name,
        description=row.description,
        allocated_tier=TierType(row.allocated_tier),
        rationale=row.rationale,
        suggested_tech=row.suggested_tech,
        user_override=bool(row.user_override),
    )


async def _replace_allocations(db: AsyncSession, session_id: str) -> list[StepAllocation]:
    existing = (
        await db.scalars(
            select(StepAllocation).where(StepAllocation.session_id == session_id)
        )
    ).all()
    for row in existing:
        await db.delete(row)
    await db.flush()
    created: list[StepAllocation] = []
    for item in stub_allocations():
        row = StepAllocation(
            id=new_id("alloc"),
            session_id=session_id,
            step_id=item["step_id"],
            step_name=item["step_name"],
            description=item["description"],
            allocated_tier=item["allocated_tier"].value,
            rationale=item["rationale"],
            suggested_tech=item["suggested_tech"],
            user_override=False,
            updated_at=utc_now(),
        )
        db.add(row)
        created.append(row)
    return created


@router.post("/{session_id}/run", response_model=list[StepAllocationOut])
async def run_allocation(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[StepAllocationOut]:
    session = await get_session_or_404(db, session_id)
    if not session.flow_approved:
        raise HTTPException(status_code=409, detail="Flow must be approved first")
    rows = await _replace_allocations(db, session_id)
    session.stage = "allocated"
    state = load_state(session)
    state["allocations"] = [
        {
            "step_id": r.step_id,
            "step_name": r.step_name,
            "allocated_tier": r.allocated_tier,
            "rationale": r.rationale,
            "suggested_tech": r.suggested_tech,
        }
        for r in rows
    ]
    save_state(session, state)
    await append_event(db, session_id, "allocation.completed")
    await db.commit()
    refreshed = (
        await db.scalars(
            select(StepAllocation)
            .where(StepAllocation.session_id == session_id)
            .order_by(StepAllocation.step_id.asc())
        )
    ).all()
    return [_out(r) for r in refreshed]


@router.get("/{session_id}", response_model=list[StepAllocationOut])
async def get_allocation(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[StepAllocationOut]:
    await get_session_or_404(db, session_id)
    rows = (
        await db.scalars(
            select(StepAllocation)
            .where(StepAllocation.session_id == session_id)
            .order_by(StepAllocation.step_id.asc())
        )
    ).all()
    return [_out(r) for r in rows]


@router.patch("/{session_id}/steps/{step_id}", response_model=StepAllocationOut)
async def override_step(
    session_id: str,
    step_id: int,
    body: AllocationOverride,
    db: AsyncSession = Depends(get_db),
) -> StepAllocationOut:
    await get_session_or_404(db, session_id)
    row = await db.scalar(
        select(StepAllocation).where(
            StepAllocation.session_id == session_id,
            StepAllocation.step_id == step_id,
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Allocation step not found")
    row.allocated_tier = body.allocated_tier.value
    row.rationale = body.rationale
    row.user_override = True
    row.updated_at = utc_now()
    await append_event(
        db, session_id, "allocation.overridden", {"step_id": step_id}
    )
    await db.commit()
    await db.refresh(row)
    return _out(row)


@router.post("/{session_id}/recompute", response_model=list[StepAllocationOut])
async def recompute(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[StepAllocationOut]:
    return await run_allocation(session_id, db)
