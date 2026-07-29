from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artifact, Package, ScaffoldJob
from app.db.session import get_db
from app.models.schemas import ArtifactOut

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


def _out(a: Artifact) -> ArtifactOut:
    return ArtifactOut(
        id=a.id,
        project_id=a.project_id,
        scaffold_job_id=a.scaffold_job_id,
        file_path=a.file_path,
        content_hash=a.content_hash,
        byte_size=a.byte_size,
        content_text=a.content_text,
        created_at=a.created_at,
    )


@router.get("", response_model=list[ArtifactOut])
async def list_artifacts(
    project_id: str, db: AsyncSession = Depends(get_db)
) -> list[ArtifactOut]:
    rows = (
        await db.scalars(
            select(Artifact)
            .where(Artifact.project_id == project_id)
            .order_by(Artifact.created_at.desc())
        )
    ).all()
    return [_out(r) for r in rows]


@router.get("/jobs/{job_id}/download")
async def download_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(ScaffoldJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    pkg = await db.scalar(
        select(Package).where(Package.scaffold_job_id == job_id)
    )
    if pkg and pkg.zip_path and Path(pkg.zip_path).exists():
        return FileResponse(
            pkg.zip_path,
            media_type="application/zip",
            filename=Path(pkg.zip_path).name,
        )
    rows = (
        await db.scalars(select(Artifact).where(Artifact.scaffold_job_id == job_id))
    ).all()
    return JSONResponse(
        content={
            "job_id": job_id,
            "status": job.status,
            "files": [
                {
                    "path": a.file_path,
                    "content_hash": a.content_hash,
                    "byte_size": a.byte_size,
                    "content": a.content_text,
                }
                for a in rows
            ],
        }
    )


@router.get("/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(
    artifact_id: str, db: AsyncSession = Depends(get_db)
) -> ArtifactOut:
    art = await db.get(Artifact, artifact_id)
    if art is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _out(art)
