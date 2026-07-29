from __future__ import annotations


async def test_connectors_and_mcp_seed(client):
    cons = await client.get("/api/v1/connectors")
    assert cons.status_code == 200
    names = {c["name"] for c in cons.json()}
    assert "Hermes Agent" in names

    hermes = next(c for c in cons.json() if c["kind"] == "hermes")
    patched = await client.patch(
        f"/api/v1/connectors/{hermes['id']}", json={"connected": True}
    )
    assert patched.status_code == 200
    assert patched.json()["connected"] is True

    tested = await client.post(f"/api/v1/connectors/{hermes['id']}/test")
    assert tested.status_code == 200
    assert "ok" in tested.json()

    mcp = await client.get("/api/v1/mcp/servers")
    assert mcp.status_code == 200
    assert len(mcp.json()) >= 1

    sid = mcp.json()[0]["id"]
    on = await client.patch(f"/api/v1/mcp/servers/{sid}", json={"enabled": True})
    assert on.status_code == 200
    assert on.json()["enabled"] is True


async def test_demo_unlock_license(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "demo_unlock", True)
    lic = await client.get("/api/v1/license")
    assert lic.status_code == 200
    body = lic.json()
    assert body["tier"] == "pro"
    assert "demo_unlock" in body["features"]
