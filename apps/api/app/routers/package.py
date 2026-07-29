from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Package, PackageFile
from app.db.session import get_db
from app.models.schemas import PackageBuildRequest, PackageFileOut, PackageOut
from app.services import package_engine
from app.services.session_helpers import get_session_or_404

router = APIRouter(prefix="/api/v1/package", tags=["package"])


async def _out(db: AsyncSession, pkg: Package) -> PackageOut:
    files = (
        await db.scalars(
            select(PackageFile).where(PackageFile.package_id == pkg.id)
        )
    ).all()
    return PackageOut(
        id=pkg.id,
        session_id=pkg.session_id,
        project_id=pkg.project_id,
        scaffold_job_id=pkg.scaffold_job_id,
        output_dir=pkg.output_dir,
        zip_path=pkg.zip_path,
        checksum_sha256=pkg.checksum_sha256,
        pytest_passed=bool(pkg.pytest_passed),
        verify_log=pkg.verify_log,
        status=pkg.status,
        files=[
            PackageFileOut(
                file_path=f.file_path, content_hash=f.content_hash, byte_size=f.byte_size
            )
            for f in files
        ],
        created_at=pkg.created_at,
    )


@router.post("/{session_id}/build", response_model=PackageOut)
async def build(
    session_id: str,
    body: PackageBuildRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> PackageOut:
    body = body or PackageBuildRequest()
    session = await get_session_or_404(db, session_id)
    try:
        pkg = await package_engine.build_package(
            db, session, output_dir=body.output_dir, run_verify=body.run_verify
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(pkg)
    return await _out(db, pkg)


@router.post("/{session_id}/verify", response_model=PackageOut)
async def verify(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> PackageOut:
    session = await get_session_or_404(db, session_id)
    pkg = await package_engine.build_package(db, session, run_verify=True)
    await db.commit()
    return await _out(db, pkg)


@router.get("/{session_id}/packages", response_model=list[PackageOut])
async def list_packages(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[PackageOut]:
    await get_session_or_404(db, session_id)
    rows = await package_engine.list_packages(db, session_id)
    return [await _out(db, r) for r in rows]
