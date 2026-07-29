"""Round-trip CRUD smoke for core SQLAlchemy entities (fastapi-models-db)."""

from __future__ import annotations

import json

from sqlalchemy import select

from app.db.init import init_db
from app.db.models import LicenseState, Project, Setting, StudioSession
from app.db.session import async_session_factory, get_engine
from app.utils.ids import new_id
from app.utils.time import utc_now


async def test_settings_license_project_session_roundtrip(client):
    factory = async_session_factory()
    async with factory() as db:
        now = utc_now()
        key = f"roundtrip_flag_{new_id('k')}"
        db.add(
            Setting(
                key=key,
                value_json=json.dumps(True),
                updated_at=now,
            )
        )
        await db.flush()
        lic = await db.get(LicenseState, 1)
        assert lic is not None
        assert lic.tier in {"free", "pro"}
        project = Project(
            id=new_id("proj"),
            name="ORM Roundtrip",
            description="smoke",
            status="draft",
            export_path=None,
            created_at=now,
            updated_at=now,
        )
        db.add(project)
        await db.flush()
        session = StudioSession(
            id=new_id("sess"),
            project_id=project.id,
            stage="created",
            raw_user_prompt="roundtrip",
            flow_approved=False,
            state_json="{}",
            token_usage=0,
            created_at=now,
            updated_at=now,
        )
        db.add(session)
        await db.commit()
        pid, sid = project.id, session.id

    async with factory() as db:
        setting = await db.get(Setting, key)
        assert setting is not None
        assert json.loads(setting.value_json) is True
        project = await db.get(Project, pid)
        assert project is not None and project.name == "ORM Roundtrip"
        session = await db.get(StudioSession, sid)
        assert session is not None and session.project_id == pid
        rows = (
            await db.scalars(
                select(StudioSession).where(StudioSession.project_id == pid)
            )
        ).all()
        assert len(rows) == 1


async def test_init_db_idempotent(client):
    engine = get_engine()
    await init_db(engine)
    await init_db(engine)
    factory = async_session_factory()
    async with factory() as db:
        lic = await db.get(LicenseState, 1)
        assert lic is not None
