from __future__ import annotations

import shutil

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/mcp/servers", tags=["mcp"])

SEED = [
    {
        "id": "mcp_filesystem",
        "name": "Filesystem",
        "transport": "stdio",
        "command": "npx",
        "args": "-y @modelcontextprotocol/server-filesystem ~/Documents",
        "url": None,
        "enabled": 0,
    },
    {
        "id": "mcp_fetch",
        "name": "Fetch",
        "transport": "stdio",
        "command": "npx",
        "args": "-y @modelcontextprotocol/server-fetch",
        "url": None,
        "enabled": 1,
    },
]


class McpServerOut(BaseModel):
    id: str
    name: str
    transport: str
    command: str | None = None
    args: str | None = None
    url: str | None = None
    enabled: bool


class McpCreate(BaseModel):
    name: str
    transport: str = "stdio"
    command: str | None = None
    args: str | None = None
    url: str | None = None


class McpPatch(BaseModel):
    enabled: bool | None = None
    name: str | None = None
    command: str | None = None
    args: str | None = None
    url: str | None = None


class TestResult(BaseModel):
    ok: bool
    message: str = ""


async def ensure_seeded(db: AsyncSession) -> None:
    row = await db.execute(text("SELECT COUNT(*) FROM mcp_servers"))
    if int(row.scalar_one()) > 0:
        return
    now = utc_now()
    for s in SEED:
        await db.execute(
            text(
                """
                INSERT INTO mcp_servers(id, name, transport, command, args, url, enabled, created_at, updated_at)
                VALUES (:id, :name, :transport, :command, :args, :url, :enabled, :created_at, :updated_at)
                """
            ),
            {**s, "created_at": now, "updated_at": now},
        )
    await db.commit()


def _row(r) -> McpServerOut:
    return McpServerOut(
        id=r.id,
        name=r.name,
        transport=r.transport,
        command=r.command,
        args=r.args,
        url=r.url,
        enabled=bool(r.enabled),
    )


@router.get("", response_model=list[McpServerOut])
async def list_servers(db: AsyncSession = Depends(get_db)) -> list[McpServerOut]:
    await ensure_seeded(db)
    result = await db.execute(
        text(
            "SELECT id, name, transport, command, args, url, enabled FROM mcp_servers ORDER BY name"
        )
    )
    return [_row(r) for r in result.fetchall()]


@router.post("", response_model=McpServerOut, status_code=201)
async def create_server(body: McpCreate, db: AsyncSession = Depends(get_db)) -> McpServerOut:
    await ensure_seeded(db)
    sid = new_id("mcp")
    now = utc_now()
    await db.execute(
        text(
            """
            INSERT INTO mcp_servers(id, name, transport, command, args, url, enabled, created_at, updated_at)
            VALUES (:id, :name, :transport, :command, :args, :url, 1, :created_at, :updated_at)
            """
        ),
        {
            "id": sid,
            "name": body.name,
            "transport": body.transport,
            "command": body.command,
            "args": body.args,
            "url": body.url,
            "created_at": now,
            "updated_at": now,
        },
    )
    await db.commit()
    return McpServerOut(
        id=sid,
        name=body.name,
        transport=body.transport,
        command=body.command,
        args=body.args,
        url=body.url,
        enabled=True,
    )


@router.patch("/{server_id}", response_model=McpServerOut)
async def update_server(
    server_id: str, body: McpPatch, db: AsyncSession = Depends(get_db)
) -> McpServerOut:
    await ensure_seeded(db)
    result = await db.execute(
        text(
            "SELECT id, name, transport, command, args, url, enabled FROM mcp_servers WHERE id = :id"
        ),
        {"id": server_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="MCP server not found")
    enabled = row.enabled if body.enabled is None else (1 if body.enabled else 0)
    name = body.name if body.name is not None else row.name
    command = body.command if body.command is not None else row.command
    args = body.args if body.args is not None else row.args
    url = body.url if body.url is not None else row.url
    await db.execute(
        text(
            """
            UPDATE mcp_servers
            SET enabled = :enabled, name = :name, command = :command, args = :args, url = :url, updated_at = :updated_at
            WHERE id = :id
            """
        ),
        {
            "id": server_id,
            "enabled": enabled,
            "name": name,
            "command": command,
            "args": args,
            "url": url,
            "updated_at": utc_now(),
        },
    )
    await db.commit()
    return McpServerOut(
        id=server_id,
        name=name,
        transport=row.transport,
        command=command,
        args=args,
        url=url,
        enabled=bool(enabled),
    )


@router.delete("/{server_id}", status_code=204)
async def delete_server(server_id: str, db: AsyncSession = Depends(get_db)) -> None:
    await ensure_seeded(db)
    await db.execute(text("DELETE FROM mcp_servers WHERE id = :id"), {"id": server_id})
    await db.commit()


@router.post("/{server_id}/test", response_model=TestResult)
async def test_server(server_id: str, db: AsyncSession = Depends(get_db)) -> TestResult:
    await ensure_seeded(db)
    result = await db.execute(
        text(
            "SELECT id, name, transport, command, args, url, enabled FROM mcp_servers WHERE id = :id"
        ),
        {"id": server_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="MCP server not found")
    if not row.enabled:
        return TestResult(ok=False, message="Turn on the server, then test")

    if row.transport in {"sse", "http"} and row.url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(row.url)
            return TestResult(
                ok=resp.status_code < 500,
                message="Looks good" if resp.status_code < 500 else f"HTTP {resp.status_code}",
            )
        except Exception as exc:  # noqa: BLE001
            return TestResult(ok=False, message=f"Couldn’t reach it — {exc}")

    cmd = (row.command or "").split()[0] if row.command else ""
    if cmd and shutil.which(cmd):
        return TestResult(ok=True, message="Looks good (command found)")
    if cmd:
        return TestResult(ok=False, message=f"Command not found: {cmd}")
    return TestResult(ok=False, message="Couldn’t reach it — check the details")
