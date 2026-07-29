from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LlmProvider, ProviderHealthCheck
from app.db.session import get_db
from app.models.schemas import (
    ProviderHealthOut,
    ProviderOrderRequest,
    ProviderOut,
    ProviderUpdate,
)
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/providers", tags=["providers"])


def _out(p: LlmProvider) -> ProviderOut:
    try:
        config = json.loads(p.config_json or "{}")
    except json.JSONDecodeError:
        config = {}
    return ProviderOut(
        id=p.id,
        name=p.name,
        enabled=bool(p.enabled),
        base_url=p.base_url,
        api_key_env_var=p.api_key_env_var,
        priority=p.priority,
        default_model=p.default_model,
        config=config,
    )


@router.get("", response_model=list[ProviderOut])
async def list_providers(db: AsyncSession = Depends(get_db)) -> list[ProviderOut]:
    rows = (
        await db.scalars(select(LlmProvider).order_by(LlmProvider.priority.asc()))
    ).all()
    return [_out(r) for r in rows]


@router.put("/order", response_model=list[ProviderOut])
async def order_providers(
    body: ProviderOrderRequest, db: AsyncSession = Depends(get_db)
) -> list[ProviderOut]:
    for idx, pid in enumerate(body.provider_ids):
        prov = await db.get(LlmProvider, pid)
        if prov is None:
            raise HTTPException(status_code=404, detail=f"Provider not found: {pid}")
        prov.priority = (idx + 1) * 10
    await db.commit()
    return await list_providers(db)


@router.patch("/{provider_id}", response_model=ProviderOut)
async def update_provider(
    provider_id: str, body: ProviderUpdate, db: AsyncSession = Depends(get_db)
) -> ProviderOut:
    prov = await db.get(LlmProvider, provider_id)
    if prov is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    if body.enabled is not None:
        prov.enabled = body.enabled
    if body.base_url is not None:
        prov.base_url = body.base_url
    if body.api_key_env_var is not None:
        prov.api_key_env_var = body.api_key_env_var
    if body.priority is not None:
        prov.priority = body.priority
    if body.default_model is not None:
        prov.default_model = body.default_model
    if body.config is not None:
        prov.config_json = json.dumps(body.config)
    await db.commit()
    await db.refresh(prov)
    return _out(prov)


@router.post("/{provider_id}/test", response_model=ProviderHealthOut)
async def test_provider(
    provider_id: str, db: AsyncSession = Depends(get_db)
) -> ProviderHealthOut:
    prov = await db.get(LlmProvider, provider_id)
    if prov is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    started = time.perf_counter()
    # Stub: ollama considered "reachable" only if enabled; no real network call
    ok = bool(prov.enabled)
    latency = int((time.perf_counter() - started) * 1000)
    message = "stub ok" if ok else "provider disabled"
    db.add(
        ProviderHealthCheck(
            id=new_id("phc"),
            provider_id=prov.id,
            ok=ok,
            latency_ms=latency,
            message=message,
            checked_at=utc_now(),
        )
    )
    await db.commit()
    return ProviderHealthOut(ok=ok, latency_ms=latency, message=message)
