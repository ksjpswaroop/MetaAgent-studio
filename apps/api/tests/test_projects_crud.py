from __future__ import annotations


async def test_project_and_session_crud(client):
    created = await client.post(
        "/api/v1/projects",
        json={"name": "Demo Agent", "description": "test"},
    )
    assert created.status_code == 201
    project = created.json()
    assert project["status"] == "draft"

    listed = await client.get("/api/v1/projects")
    assert any(p["id"] == project["id"] for p in listed.json())

    session = await client.post(
        "/api/v1/sessions",
        json={
            "project_id": project["id"],
            "raw_user_prompt": "Build a support triage agent",
        },
    )
    assert session.status_code == 201
    sess = session.json()
    assert sess["stage"] == "created"

    got = await client.get(f"/api/v1/sessions/{sess['id']}")
    assert got.status_code == 200
    assert got.json()["raw_user_prompt"].startswith("Build a support")

    archived = await client.delete(f"/api/v1/projects/{project['id']}")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
