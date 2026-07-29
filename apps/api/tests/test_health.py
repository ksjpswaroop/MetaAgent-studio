from __future__ import annotations


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["db_ok"] is True
    assert data["status"] == "ok"
    assert "version" in data
