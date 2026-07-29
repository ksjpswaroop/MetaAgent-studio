from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])

SEED = [
    {
        "id": "conn_hermes",
        "kind": "hermes",
        "name": "Hermes Agent",
        "description": "Run and hand off work to a Hermes agent",
        "connected": 0,
        "base_url": "http://127.0.0.1:8787",
    },
    {
        "id": "conn_gmail",
        "kind": "gmail",
        "name": "Gmail",
        "description": "Read and draft email",
        "connected": 0,
        "base_url": None,
    },
    {
        "id": "conn_slack",
        "kind": "slack",
        "name": "Slack",
        "description": "Post messages to channels",
        "connected": 0,
        "base_url": None,
    },
    {
        "id": "conn_notion",
        "kind": "notion",
        "name": "Notion",
        "description": "Search pages and notes",
        "connected": 0,
        "base_url": None,
    },
    {
        "id": "conn_sheets",
        "kind": "sheets",
        "name": "Google Sheets",
        "description": "Read and update rows",
        "connected": 0,
        "base_url": None,
    },
    {
        "id": "conn_webhook",
        "kind": "webhook",
        "name": "Webhook",
        "description": "Call your own HTTP endpoint",
        "connected": 0,
        "base_url": "https://example.com/hook",
    },
]


class ConnectorOut(BaseModel):
    id: str
    kind: str
    name: str
    description: str
    connected: bool
    baseUrl: str | None = None


class ConnectorCreate(BaseModel):
    name: str
    kind: str = "custom"
    base_url: str | None = None


class ConnectorPatch(BaseModel):
    connected: bool | None = None
    base_url: str | None = None


class TestResult(BaseModel):
    ok: bool
    message: str = ""


async def ensure_seeded(db: AsyncSession) -> None:
    row = await db.execute(text("SELECT COUNT(*) FROM connectors"))
    if int(row.scalar_one()) > 0:
        return
    now = utc_now()
    for c in SEED:
        await db.execute(
            text(
                """
                INSERT INTO connectors(id, kind, name, description, connected, base_url, created_at, updated_at)
                VALUES (:id, :kind, :name, :description, :connected, :base_url, :created_at, :updated_at)
                """
            ),
            {**c, "created_at": now, "updated_at": now},
        )
    await db.commit()


def _row(r) -> ConnectorOut:
    return ConnectorOut(
        id=r.id,
        kind=r.kind,
        name=r.name,
        description=r.description or "",
        connected=bool(r.connected),
        baseUrl=r.base_url,
    )


@router.get("", response_model=list[ConnectorOut])
async def list_connectors(db: AsyncSession = Depends(get_db)) -> list[ConnectorOut]:
    await ensure_seeded(db)
    result = await db.execute(
        text("SELECT id, kind, name, description, connected, base_url FROM connectors ORDER BY name")
    )
    return [_row(r) for r in result.fetchall()]


@router.post("", response_model=ConnectorOut, status_code=201)
async def create_connector(
    body: ConnectorCreate, db: AsyncSession = Depends(get_db)
) -> ConnectorOut:
    await ensure_seeded(db)
    cid = new_id("conn")
    now = utc_now()
    await db.execute(
        text(
            """
            INSERT INTO connectors(id, kind, name, description, connected, base_url, created_at, updated_at)
            VALUES (:id, :kind, :name, :description, 1, :base_url, :created_at, :updated_at)
            """
        ),
        {
            "id": cid,
            "kind": body.kind,
            "name": body.name,
            "description": "Custom REST connector",
            "base_url": body.base_url,
            "created_at": now,
            "updated_at": now,
        },
    )
    await db.commit()
    return ConnectorOut(
        id=cid,
        kind=body.kind,
        name=body.name,
        description="Custom REST connector",
        connected=True,
        baseUrl=body.base_url,
    )


@router.patch("/{connector_id}", response_model=ConnectorOut)
async def update_connector(
    connector_id: str, body: ConnectorPatch, db: AsyncSession = Depends(get_db)
) -> ConnectorOut:
    await ensure_seeded(db)
    result = await db.execute(
        text(
            "SELECT id, kind, name, description, connected, base_url FROM connectors WHERE id = :id"
        ),
        {"id": connector_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Connector not found")
    connected = row.connected if body.connected is None else (1 if body.connected else 0)
    base_url = row.base_url if body.base_url is None else body.base_url
    await db.execute(
        text(
            """
            UPDATE connectors SET connected = :connected, base_url = :base_url, updated_at = :updated_at
            WHERE id = :id
            """
        ),
        {
            "id": connector_id,
            "connected": connected,
            "base_url": base_url,
            "updated_at": utc_now(),
        },
    )
    await db.commit()
    return ConnectorOut(
        id=row.id,
        kind=row.kind,
        name=row.name,
        description=row.description or "",
        connected=bool(connected),
        baseUrl=base_url,
    )


@router.post("/{connector_id}/test", response_model=TestResult)
async def test_connector(
    connector_id: str, db: AsyncSession = Depends(get_db)
) -> TestResult:
    await ensure_seeded(db)
    result = await db.execute(
        text(
            "SELECT id, kind, name, connected, base_url FROM connectors WHERE id = :id"
        ),
        {"id": connector_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Connector not found")

    if row.kind in {"hermes", "webhook", "custom"} and row.base_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(row.base_url)
            return TestResult(
                ok=resp.status_code < 500,
                message="Looks good" if resp.status_code < 500 else f"HTTP {resp.status_code}",
            )
        except Exception as exc:  # noqa: BLE001
            # Hermes may be offline — still allow "connected" mock success for demo
            if row.kind == "hermes" and row.connected:
                return TestResult(
                    ok=True,
                    message="Hermes endpoint unreachable; marked ready for demo handoff",
                )
            return TestResult(ok=False, message=f"Couldn’t reach it — {exc}")

    if row.connected:
        return TestResult(ok=True, message="Looks good (local stub)")
    return TestResult(ok=False, message="Connect first, then test")
