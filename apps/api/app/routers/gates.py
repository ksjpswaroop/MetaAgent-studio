from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GateConfig, GateRun
from app.db.session import get_db
from app.models.schemas import GateConfigOut, GateRunOut, GateUpdate
from app.services.session_helpers import append_event, get_session_or_404
from app.utils.ids import new_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/v1/gates", tags=["gates"])

DEFAULT_GATES = [
    ("schema", "pre", {"strict": True}),
    ("pii", "post", {"redact": ["email", "phone"]}),
    ("cost_budget", "pre", {"max_tokens": 15000}),
    ("rate_limit", "pre", {"rpm": 60}),
]


def _gate_out(g: GateConfig) -> GateConfigOut:
    return GateConfigOut(
        id=g.id,
        gate_type=g.gate_type,
        phase=g.phase,
        enabled=bool(g.enabled),
        config=json.loads(g.config_json or "{}"),
    )


async def _ensure_defaults(db: AsyncSession, session_id: str) -> list[GateConfig]:
    rows = list(
        (
            await db.scalars(
                select(GateConfig).where(GateConfig.session_id == session_id)
            )
        ).all()
    )
    if rows:
        return rows
    created: list[GateConfig] = []
    for gate_type, phase, config in DEFAULT_GATES:
        g = GateConfig(
            id=new_id("gate"),
            session_id=session_id,
            gate_type=gate_type,
            phase=phase,
            enabled=True,
            config_json=json.dumps(config),
            created_at=utc_now(),
        )
        db.add(g)
        created.append(g)
    await db.commit()
    return created


@router.get("/{session_id}", response_model=list[GateConfigOut])
async def list_gates(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[GateConfigOut]:
    await get_session_or_404(db, session_id)
    rows = await _ensure_defaults(db, session_id)
    return [_gate_out(g) for g in rows]


@router.patch("/{session_id}/configs/{gate_id}", response_model=GateConfigOut)
async def update_gate(
    session_id: str,
    gate_id: str,
    body: GateUpdate,
    db: AsyncSession = Depends(get_db),
) -> GateConfigOut:
    await get_session_or_404(db, session_id)
    gate = await db.get(GateConfig, gate_id)
    if gate is None or gate.session_id != session_id:
        raise HTTPException(status_code=404, detail="Gate not found")
    if body.enabled is not None:
        gate.enabled = body.enabled
    if body.config is not None:
        gate.config_json = json.dumps(body.config)
    await db.commit()
    await db.refresh(gate)
    return _gate_out(gate)


@router.post("/{session_id}/dry-run", response_model=list[GateRunOut])
async def dry_run(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[GateRunOut]:
    session = await get_session_or_404(db, session_id)
    gates = await _ensure_defaults(db, session_id)
    runs: list[GateRun] = []
    for g in gates:
        if not g.enabled:
            continue
        run = GateRun(
            id=new_id("grun"),
            session_id=session_id,
            gate_config_id=g.id,
            passed=True,
            details_json=json.dumps({"gate_type": g.gate_type, "stub": True}),
            created_at=utc_now(),
        )
        db.add(run)
        runs.append(run)
    session.stage = "gated"
    await append_event(db, session_id, "gates.dry_run")
    await db.commit()
    return [
        GateRunOut(
            id=r.id,
            gate_config_id=r.gate_config_id,
            passed=bool(r.passed),
            details=json.loads(r.details_json or "{}"),
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get("/{session_id}/runs", response_model=list[GateRunOut])
async def list_runs(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[GateRunOut]:
    await get_session_or_404(db, session_id)
    rows = (
        await db.scalars(
            select(GateRun)
            .where(GateRun.session_id == session_id)
            .order_by(GateRun.created_at.desc())
        )
    ).all()
    return [
        GateRunOut(
            id=r.id,
            gate_config_id=r.gate_config_id,
            passed=bool(r.passed),
            details=json.loads(r.details_json or "{}"),
            created_at=r.created_at,
        )
        for r in rows
    ]
