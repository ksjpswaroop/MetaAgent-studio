from __future__ import annotations


async def _pipeline(client):
    project = (
        await client.post("/api/v1/projects", json={"name": "Pipeline"})
    ).json()
    session = (
        await client.post(
            "/api/v1/sessions",
            json={"project_id": project["id"], "raw_user_prompt": "triage emails"},
        )
    ).json()
    sid = session["id"]

    await client.post(f"/api/v1/discovery/{sid}/start")
    await client.post(
        f"/api/v1/discovery/{sid}/answer",
        json={"question_key": "trigger_type", "answer": "webhook"},
    )
    scope = await client.post(
        f"/api/v1/discovery/{sid}/finalize",
        json={
            "scope": {
                "project_name": "Pipeline",
                "primary_goal": "Triage support email",
                "trigger_type": "webhook",
                "external_tools": ["zendesk"],
                "human_in_loop": True,
                "fallback_strategy": "queue retry",
            }
        },
    )
    assert scope.status_code == 200

    flows = await client.post(f"/api/v1/flows/{sid}/generate")
    assert flows.status_code == 200
    assert len(flows.json()) == 3

    blocked = await client.post(f"/api/v1/allocation/{sid}/run")
    assert blocked.status_code == 409

    approved = await client.post(f"/api/v1/flows/{sid}/approve")
    assert approved.status_code == 200

    alloc = await client.post(f"/api/v1/allocation/{sid}/run")
    assert alloc.status_code == 200
    assert len(alloc.json()) >= 3

    arch = await client.post(f"/api/v1/architecture/{sid}/build")
    assert arch.status_code == 200
    assert arch.json()["tools"]

    gates = await client.post(f"/api/v1/gates/{sid}/dry-run")
    assert gates.status_code == 200

    job = await client.post(f"/api/v1/scaffold/{sid}/run", json={})
    assert job.status_code == 200
    assert job.json()["status"] == "passed"
    assert job.json()["file_map"]

    arts = await client.get(f"/api/v1/artifacts?project_id={project['id']}")
    assert arts.status_code == 200
    assert len(arts.json()) > 0
    return sid, job.json()["id"]


async def test_full_stub_pipeline(client):
    await _pipeline(client)


async def test_settings_and_providers(client):
    settings = await client.get("/api/v1/settings")
    assert settings.status_code == 200
    assert "token_budget" in settings.json()

    updated = await client.put(
        "/api/v1/settings", json={"token_budget": 12000, "telemetry_enabled": False}
    )
    assert updated.status_code == 200
    assert updated.json()["token_budget"] == 12000

    providers = await client.get("/api/v1/providers")
    assert providers.status_code == 200
    oid = providers.json()[0]["id"]
    health = await client.post(f"/api/v1/providers/{oid}/test")
    assert health.status_code == 200
