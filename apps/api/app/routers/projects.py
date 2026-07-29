from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project
from app.db.session import get_db
from app.models.schemas import ProjectCreate, ProjectOut, ProjectUpdate
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _to_out(p: Project) -> ProjectOut:
    return ProjectOut(
        id=p.id,
        name=p.name,
        description=p.description,
        status=p.status,
        export_path=p.export_path,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)) -> list[ProjectOut]:
    rows = (
        await db.scalars(select(Project).order_by(Project.created_at.desc()))
    ).all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate, db: AsyncSession = Depends(get_db)
) -> ProjectOut:
    now = utc_now()
    project = Project(
        id=new_id("proj"),
        name=body.name,
        description=body.description,
        status="draft",
        export_path=body.export_path,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return _to_out(project)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str, db: AsyncSession = Depends(get_db)
) -> ProjectOut:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _to_out(project)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str, body: ProjectUpdate, db: AsyncSession = Depends(get_db)
) -> ProjectOut:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.status is not None:
        project.status = body.status.value
    if body.export_path is not None:
        project.export_path = body.export_path
    project.updated_at = utc_now()
    await db.commit()
    await db.refresh(project)
    return _to_out(project)


@router.delete("/{project_id}", response_model=ProjectOut)
async def archive_project(
    project_id: str, db: AsyncSession = Depends(get_db)
) -> ProjectOut:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = "archived"
    project.updated_at = utc_now()
    await db.commit()
    await db.refresh(project)
    return _to_out(project)
