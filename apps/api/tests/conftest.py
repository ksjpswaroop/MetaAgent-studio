from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PROJECTS = json.loads((FIXTURES / "sample_projects.json").read_text())

TEST_DB = Path("/tmp/metaagent-studio-pytest.db")
TEST_EXPORT = Path("/tmp/metaagent-exports-pytest")


def pytest_configure():
    os.environ["METAAGENT_DB_PATH"] = str(TEST_DB)
    os.environ["METAAGENT_LLM_MODE"] = os.environ.get("METAAGENT_LLM_MODE", "cassette")
    os.environ["METAAGENT_DEFAULT_EXPORT_PATH"] = str(TEST_EXPORT)
    os.environ["METAAGENT_LLM_CASSETTE_DIR"] = str(FIXTURES / "llm")


# Import app after env is set
from app.config import settings  # noqa: E402
from app.db.session import reset_engine  # noqa: E402
from app.main import app  # noqa: E402

settings.llm_mode = os.environ.get("METAAGENT_LLM_MODE", "cassette")
settings.llm_cassette_dir = FIXTURES / "llm"
settings.default_export_path = str(TEST_EXPORT)


@pytest.fixture(autouse=True)
async def fresh_db(tmp_path):
    reset_engine()
    if TEST_DB.exists():
        TEST_DB.unlink()
    for suffix in ("-wal", "-shm"):
        p = Path(str(TEST_DB) + suffix)
        if p.exists():
            p.unlink()
    TEST_EXPORT.mkdir(parents=True, exist_ok=True)
    yield
    reset_engine()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with app.router.lifespan_context(app):
            yield ac


async def create_project_session(client: AsyncClient, name: str, prompt: str):
    project = (
        await client.post("/api/v1/projects", json={"name": name, "description": prompt})
    ).json()
    session = (
        await client.post(
            "/api/v1/sessions",
            json={"project_id": project["id"], "raw_user_prompt": prompt},
        )
    ).json()
    return project, session


async def run_to_stage(client: AsyncClient, session_id: str, stage: str):
    """Advance a session through design stages up to and including `stage`."""
    order = [
        "discovery",
        "scope_ready",
        "flows",
        "flow_approved",
        "allocated",
        "architected",
        "gated",
        "scaffolded",
    ]
    target = order.index(stage)

    if target >= 0:
        await client.post(f"/api/v1/discovery/{session_id}/start")
        await client.post(
            f"/api/v1/discovery/{session_id}/answer",
            json={"question_key": "trigger_type", "answer": "webhook"},
        )
    if target >= 1:
        fin = await client.post(f"/api/v1/discovery/{session_id}/finalize", json={})
        assert fin.status_code == 200, fin.text
    if target >= 2:
        gen = await client.post(f"/api/v1/flows/{session_id}/generate")
        assert gen.status_code == 200, gen.text
    if target >= 3:
        appr = await client.post(f"/api/v1/flows/{session_id}/approve")
        assert appr.status_code == 200, appr.text
    if target >= 4:
        alloc = await client.post(f"/api/v1/allocation/{session_id}/run")
        assert alloc.status_code == 200, alloc.text
    if target >= 5:
        arch = await client.post(f"/api/v1/architecture/{session_id}/build")
        assert arch.status_code == 200, arch.text
    if target >= 6:
        gates = await client.post(f"/api/v1/gates/{session_id}/dry-run")
        assert gates.status_code == 200, gates.text
    if target >= 7:
        sc = await client.post(f"/api/v1/scaffold/{session_id}/run", json={})
        assert sc.status_code == 200, sc.text
    return await client.get(f"/api/v1/sessions/{session_id}")
