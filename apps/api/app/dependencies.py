from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import license_service


async def require_pro_license(db: AsyncSession = Depends(get_db)) -> None:
    if not await license_service.is_pro_active(db):
        raise HTTPException(
            status_code=402,
            detail="Pro license required. Activate a key via POST /api/v1/license/activate",
        )
