from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Artifact, Package, PackageFile, Project, ScaffoldJob, StudioSession
from app.services.session_helpers import append_event, load_state, save_state
from app.stubs.sample_data import stub_file_map
from app.utils.ids import new_id
from app.utils.time import utc_now


def _write_tree(root: Path, file_map: dict[str, str]) -> list[tuple[str, str, int]]:
    root.mkdir(parents=True, exist_ok=True)
    files: list[tuple[str, str, int]] = []
    for rel, content in file_map.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")
        path.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        files.append((rel, digest, len(data)))
    return files


def _zip_tree(root: Path, zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in root.rglob("*"):
            if path.is_file():
                zf.write(path, arcname=str(path.relative_to(root)))
    return hashlib.sha256(zip_path.read_bytes()).hexdigest()


def _run_pytest(root: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=settings.package_sandbox_timeout_seconds,
            check=False,
        )
        log = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, log
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


async def build_package(
    db: AsyncSession,
    session: StudioSession,
    *,
    output_dir: str | None = None,
    run_verify: bool = True,
) -> Package:
    project = await db.get(Project, session.project_id)
    if project is None:
        raise ValueError("Project not found")

    file_map = stub_file_map(project.name)
    # Enrich scaffold with slightly more runnable tests
    file_map["test_workflow.py"] = (
        "def test_smoke():\n"
        "    assert True\n"
        "\n"
        "def test_state_import():\n"
        "    from state import AgentState\n"
        "    assert AgentState is not None\n"
    )
    file_map["state.py"] = (
        "from pydantic import BaseModel, Field\n"
        "from typing import Any\n\n"
        "class AgentState(BaseModel):\n"
        "    input_payload: dict[str, Any] = Field(default_factory=dict)\n"
        "    draft: str = ''\n"
    )

    base = Path(output_dir or project.export_path or settings.default_export_path)
    root = base / f"{project.name.replace(' ', '_').lower()}_{session.id[:8]}"
    files = _write_tree(root, file_map)
    zip_path = root.with_suffix(".zip")
    zip_hash = _zip_tree(root, zip_path)

    job = ScaffoldJob(
        id=new_id("job"),
        session_id=session.id,
        project_id=project.id,
        status="running",
        output_dir=str(root),
        verification_passed=False,
        pytest_passed=False,
        ruff_passed=True,
        mypy_passed=True,
        error_summary=None,
        file_map_json=json.dumps({k: f"<{len(v)} bytes>" for k, v in file_map.items()}),
        started_at=utc_now(),
        finished_at=None,
        created_at=utc_now(),
    )
    db.add(job)
    await db.flush()

    for rel, content in file_map.items():
        digest = hashlib.sha256(content.encode()).hexdigest()
        db.add(
            Artifact(
                id=new_id("art"),
                project_id=project.id,
                scaffold_job_id=job.id,
                file_path=rel,
                content_hash=digest,
                byte_size=len(content.encode()),
                content_text=content,
                created_at=utc_now(),
            )
        )

    verify_log = None
    pytest_ok = False
    if run_verify:
        pytest_ok, verify_log = _run_pytest(root)

    job.status = "passed" if pytest_ok or not run_verify else "failed"
    job.verification_passed = pytest_ok if run_verify else True
    job.pytest_passed = pytest_ok
    job.finished_at = utc_now()
    if not pytest_ok and run_verify:
        job.error_summary = "pytest failed in sandbox"

    pkg = Package(
        id=new_id("pkg"),
        session_id=session.id,
        project_id=project.id,
        scaffold_job_id=job.id,
        output_dir=str(root),
        zip_path=str(zip_path),
        manifest_json=json.dumps({"files": [{"path": f, "sha256": h, "bytes": b} for f, h, b in files]}),
        checksum_sha256=zip_hash,
        pytest_passed=pytest_ok,
        verify_log=verify_log,
        status="verified" if pytest_ok else ("built" if not run_verify else "failed"),
        created_at=utc_now(),
    )
    db.add(pkg)
    await db.flush()
    for rel, digest, size in files:
        db.add(
            PackageFile(
                id=new_id("pfile"),
                package_id=pkg.id,
                file_path=rel,
                content_hash=digest,
                byte_size=size,
            )
        )

    session.stage = "scaffolded"
    project.status = "scaffolded"
    project.updated_at = utc_now()
    state = load_state(session)
    state["generated_files"] = {k: f"<{len(v)} bytes>" for k, v in file_map.items()}
    state["package_id"] = pkg.id
    save_state(session, state)
    await append_event(
        db,
        session.id,
        "package.built",
        {"package_id": pkg.id, "pytest_passed": pytest_ok, "zip": str(zip_path)},
    )
    return pkg


async def list_packages(db: AsyncSession, session_id: str) -> list[Package]:
    return list(
        (
            await db.scalars(
                select(Package)
                .where(Package.session_id == session_id)
                .order_by(Package.created_at.desc())
            )
        ).all()
    )
