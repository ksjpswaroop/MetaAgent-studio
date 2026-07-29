from __future__ import annotations


async def test_license_activate_deactivate(client):
    bad = await client.post(
        "/api/v1/license/activate", json={"license_key": "not-a-valid-key"}
    )
    assert bad.status_code == 400

    ok = await client.post(
        "/api/v1/license/activate",
        json={"license_key": "MAS-PRO-TEST-KEY1-ABCD"},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["tier"] == "pro"
    assert body["status"] == "active"
    assert body["license_key_last4"] == "ABCD"
    assert "teams" in body["features"]

    pro = await client.get("/api/v1/teams")
    assert pro.status_code == 200

    off = await client.post("/api/v1/license/deactivate")
    assert off.status_code == 200
    assert off.json()["tier"] == "free"

    blocked = await client.get("/api/v1/teams")
    assert blocked.status_code == 402
