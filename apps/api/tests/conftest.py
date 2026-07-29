from __future__ import annotations

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Configure DB before app imports engine
TEST_DB = Path("/tmp/metaagent-studio-pytest.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["METAAGENT_DB_PATH"] = str(TEST_DB)

from app.db.session import reset_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
async def fresh_db():
    reset_engine()
    if TEST_DB.exists():
        TEST_DB.unlink()
    # also remove wal/shm
    for suffix in ("-wal", "-shm"):
        p = Path(str(TEST_DB) + suffix)
        if p.exists():
            p.unlink()
    yield
    reset_engine()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # trigger lifespan
        async with app.router.lifespan_context(app):
            yield ac
