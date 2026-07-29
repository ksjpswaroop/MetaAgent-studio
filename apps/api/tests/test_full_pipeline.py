from __future__ import annotations

from pathlib import Path

from conftest import SAMPLE_PROJECTS, create_project_session, run_to_stage


async def test_cassette_pipeline_and_package(client, tmp_path):
    sample = SAMPLE_PROJECTS[0]
    project, session = await create_project_session(
        client, sample["name"], sample["prompt"]
    )
    sid = session["id"]

    # Design stages via LLM cassette engines
    resp = await run_to_stage(client, sid, "architected")
    assert resp.status_code == 200
    assert resp.json()["stage"] == "architected"

    gates = await client.post(f"/api/v1/gates/{sid}/dry-run")
    assert gates.status_code == 200
    assert all(r["passed"] for r in gates.json())

    pkg = await client.post(
        f"/api/v1/package/{sid}/build",
        json={"output_dir": str(tmp_path / "exports"), "run_verify": True},
    )
    assert pkg.status_code == 200, pkg.text
    body = pkg.json()
    assert body["checksum_sha256"]
    assert Path(body["zip_path"]).exists()
    assert body["pytest_passed"] is True
    assert len(body["files"]) >= 3

    arts = await client.get(f"/api/v1/artifacts?project_id={project['id']}")
    assert arts.status_code == 200
    assert len(arts.json()) > 0


async def test_edge_sim_prompts_improve_pack(client, tmp_path):
    sample = SAMPLE_PROJECTS[1]
    _, session = await create_project_session(client, sample["name"], sample["prompt"])
    sid = session["id"]
    await run_to_stage(client, sid, "architected")

    edges = await client.post(
        f"/api/v1/edge-cases/{sid}/generate", json={"count": 3}
    )
    assert edges.status_code == 200
    assert len(edges.json()) >= 1
    case_id = edges.json()[0]["id"]

    attached = await client.post(
        f"/api/v1/edge-cases/{sid}/{case_id}/attach-to-flows"
    )
    assert attached.status_code == 200
    assert attached.json()["attached_scenario_id"]

    sim = await client.post(
        f"/api/v1/simulate/{sid}/run",
        json={"include_all_scenarios": True, "edge_case_ids": [case_id]},
    )
    assert sim.status_code == 200, sim.text
    run = sim.json()
    assert run["status"] in {"passed", "partial", "failed"}
    assert "overall" in run["score"]
    assert run["traces"]

    prompts = await client.post(
        f"/api/v1/prompts/{sid}/generate",
        json={"simulation_run_id": run["id"], "tool_target": "cursor"},
    )
    assert prompts.status_code == 200
    assert prompts.json()[0]["prompt_text"]
    assert prompts.json()[0]["tool_target"] == "cursor"

    await client.post(
        f"/api/v1/package/{sid}/build",
        json={"output_dir": str(tmp_path / "exp2"), "run_verify": True},
    )

    it = await client.post(
        f"/api/v1/improve/{sid}/iterate",
        json={"auto_attach_edge_cases": True, "generate_prompts": True},
    )
    assert it.status_code == 200, it.text
    assert it.json()["iteration_index"] == 1
    assert it.json()["score_after"] is not None

    hist = await client.get(f"/api/v1/improve/{sid}/history")
    assert len(hist.json()) == 1

    pub = await client.post(
        f"/api/v1/improve/{sid}/publish-local",
        json={"name": "Invoice Pack v1"},
    )
    assert pub.status_code == 200
    pack_id = pub.json()["id"]

    packs = await client.get("/api/v1/packs")
    assert any(p["id"] == pack_id for p in packs.json())

    forked = await client.post(
        f"/api/v1/packs/{pack_id}/fork",
        json={"project_name": "Invoice Fork"},
    )
    assert forked.status_code == 200
    assert forked.json()["state"]["forked_pack_id"] == pack_id


async def test_allocation_requires_approval(client):
    _, session = await create_project_session(client, "X", "y")
    sid = session["id"]
    await run_to_stage(client, sid, "flows")
    blocked = await client.post(f"/api/v1/allocation/{sid}/run")
    assert blocked.status_code == 409
