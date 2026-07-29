from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.config import settings


def _key(task: str, user: str) -> str:
    digest = hashlib.sha256(f"{task}:{user}".encode()).hexdigest()[:16]
    return f"{task}_{digest}.json"


def cassette_path(task: str, user: str) -> Path:
    return Path(settings.llm_cassette_dir) / _key(task, user)


def load_cassette(task: str, user: str) -> dict[str, Any] | None:
    path = cassette_path(task, user)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    # Fall back to task-default cassette
    default = Path(settings.llm_cassette_dir) / f"{task}_default.json"
    if default.exists():
        return json.loads(default.read_text(encoding="utf-8"))
    return None


def save_cassette(task: str, user: str, payload: dict[str, Any]) -> None:
    path = cassette_path(task, user)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
