from __future__ import annotations

from sqlalchemy import text

from app.db.session import get_engine


async def test_core_tables_exist(client):
    engine = get_engine()
    async with engine.connect() as conn:
        rows = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        names = {r[0] for r in rows.fetchall()}
    for required in {
        "app_meta",
        "license_state",
        "settings",
        "projects",
        "studio_sessions",
        "scope_envelopes",
        "execution_scenarios",
        "step_allocations",
        "architecture_blueprints",
        "scaffold_jobs",
        "artifacts",
        "llm_providers",
    }:
        assert required in names


async def test_seed_providers_and_license(client):
    lic = await client.get("/api/v1/license")
    assert lic.status_code == 200
    assert lic.json()["tier"] == "free"
    providers = await client.get("/api/v1/providers")
    assert providers.status_code == 200
    names = {p["name"] for p in providers.json()}
    assert "ollama" in names
