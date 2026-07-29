from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ArchitectureBlueprint, ScaffoldJob
from app.db.session import get_db
from app.models.schemas import ScaffoldJobOut, ScaffoldRunRequest
from app.services import package_engine
from app.services.session_helpers import get_session_or_404

router = APIRouter(prefix="/api/v1/scaffold", tags=["scaffold"])


def _job_out(job: ScaffoldJob) -> ScaffoldJobOut:
    try:
        file_map = json.loads(job.file_map_json or "{}")
    except json.JSONDecodeError:
        file_map = {}
    return ScaffoldJobOut(
        id=job.id,
        session_id=job.session_id,
        project_id=job.project_id,
        status=job.status,
        output_dir=job.output_dir,
        verification_passed=bool(job.verification_passed),
        pytest_passed=bool(job.pytest_passed),
        ruff_passed=bool(job.ruff_passed),
        mypy_passed=bool(job.mypy_passed),
        error_summary=job.error_summary,
        file_map=file_map,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.post("/{session_id}/run", response_model=ScaffoldJobOut)
async def run_scaffold(
    session_id: str,
    body: ScaffoldRunRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ScaffoldJobOut:
    body = body or ScaffoldRunRequest()
    session = await get_session_or_404(db, session_id)
    bp = await db.scalar(
        select(ArchitectureBlueprint).where(
            ArchitectureBlueprint.session_id == session_id
        )
    )
    if bp is None:
        raise HTTPException(status_code=409, detail="Architecture blueprint required")
    pkg = await package_engine.build_package(
        db,
        session,
        output_dir=body.output_dir,
        run_verify=True,
    )
    await db.commit()
    job = await db.get(ScaffoldJob, pkg.scaffold_job_id)
    if job is None:
        raise HTTPException(status_code=500, detail="Scaffold job missing after package")
    return _job_out(job)


@router.get("/{session_id}/jobs", response_model=list[ScaffoldJobOut])
async def list_jobs(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ScaffoldJobOut]:
    await get_session_or_404(db, session_id)
    rows = (
        await db.scalars(
            select(ScaffoldJob)
            .where(ScaffoldJob.session_id == session_id)
            .order_by(ScaffoldJob.created_at.desc())
        )
    ).all()
    return [_job_out(r) for r in rows]


@router.get("/jobs/{job_id}", response_model=ScaffoldJobOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)) -> ScaffoldJobOut:
    job = await db.get(ScaffoldJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_out(job)
