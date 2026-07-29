from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Setting
from app.db.session import get_db
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    rows = (await db.scalars(select(Setting))).all()
    out: dict[str, Any] = {}
    for r in rows:
        try:
            out[r.key] = json.loads(r.value_json)
        except json.JSONDecodeError:
            out[r.key] = r.value_json
    return out


@router.put("")
async def put_settings(
    body: dict[str, Any], db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    now = utc_now()
    for key, value in body.items():
        row = await db.get(Setting, key)
        encoded = json.dumps(value)
        if row is None:
            db.add(Setting(key=key, value_json=encoded, updated_at=now))
        else:
            row.value_json = encoded
            row.updated_at = now
    await db.commit()
    return await get_settings(db)
