from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.config import settings
from app.db.session import get_db
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    providers_reachable = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(settings.ollama_base_url.rstrip("/") + "/api/tags")
            providers_reachable = resp.status_code == 200
    except Exception:
        providers_reachable = False

    return HealthResponse(
        status="ok" if db_ok else "error",
        version=__version__,
        db_ok=db_ok,
        providers_reachable=providers_reachable,
        demo_unlock=settings.demo_unlock,
        llm_mode=settings.llm_mode,
    )
