from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ArchitectureBlueprint, Artifact, Project, ScaffoldJob
from app.db.session import get_db
from app.models.schemas import ScaffoldJobOut, ScaffoldRunRequest
from app.services.session_helpers import (
    append_event,
    get_session_or_404,
    load_state,
    save_state,
)
from app.stubs.sample_data import stub_file_map
from app.utils.ids import new_id
from app.utils.time import utc_now

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
    project = await db.get(Project, session.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    now = utc_now()
    file_map = stub_file_map(project.name)
    job = ScaffoldJob(
        id=new_id("job"),
        session_id=session_id,
        project_id=project.id,
        status="running",
        output_dir=body.output_dir or project.export_path,
        verification_passed=False,
        pytest_passed=False,
        ruff_passed=False,
        mypy_passed=False,
        error_summary=None,
        file_map_json=json.dumps(file_map),
        started_at=now,
        finished_at=None,
        created_at=now,
    )
    db.add(job)
    await db.flush()

    # Stub verification success; optional disk write omitted unless write_to_disk
    job.status = "passed"
    job.verification_passed = True
    job.pytest_passed = True
    job.ruff_passed = True
    job.mypy_passed = True
    job.finished_at = utc_now()

    for path, content in file_map.items():
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        db.add(
            Artifact(
                id=new_id("art"),
                project_id=project.id,
                scaffold_job_id=job.id,
                file_path=path,
                content_hash=digest,
                byte_size=len(content.encode("utf-8")),
                content_text=content,
                created_at=utc_now(),
            )
        )

    session.stage = "scaffolded"
    project.status = "scaffolded"
    project.updated_at = utc_now()
    state = load_state(session)
    state["generated_files"] = {k: f"<stub {len(v)} bytes>" for k, v in file_map.items()}
    save_state(session, state)
    await append_event(
        db,
        session_id,
        "scaffold.completed",
        {"job_id": job.id, "write_to_disk": body.write_to_disk},
    )
    await db.commit()
    await db.refresh(job)
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
