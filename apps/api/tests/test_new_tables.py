from __future__ import annotations

from sqlalchemy import text

from app.db.session import get_engine


async def test_migration_002_tables(client):
    engine = get_engine()
    async with engine.connect() as conn:
        rows = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        names = {r[0] for r in rows.fetchall()}
    for required in {
        "edge_cases",
        "simulation_runs",
        "simulation_step_traces",
        "coding_gap_prompts",
        "packages",
        "package_files",
        "improvement_iterations",
        "agent_packs",
    }:
        assert required in names
