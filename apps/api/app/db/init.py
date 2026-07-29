from __future__ import annotations

import json
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.config import settings
from app.db.session import get_engine
from app.utils.time import utc_now


SCHEMA_PATH = Path(__file__).with_name("schema.sql")
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

DEFAULT_SETTINGS = {
    "export_path": settings.default_export_path,
    "token_budget": settings.token_budget,
    "http_timeout_seconds": settings.http_timeout_seconds,
    "default_model": "qwen2.5-coder:1.5b",
    "telemetry_enabled": False,
}

DEFAULT_PROVIDERS = [
    {
        "id": "prov_ollama",
        "name": "ollama",
        "enabled": 1,
        "base_url": "http://127.0.0.1:11434",
        "api_key_env_var": None,
        "priority": 10,
        "default_model": "qwen2.5-coder:1.5b",
    },
    {
        "id": "prov_anthropic",
        "name": "anthropic",
        "enabled": 0,
        "base_url": "https://api.anthropic.com",
        "api_key_env_var": "ANTHROPIC_API_KEY",
        "priority": 20,
        "default_model": "claude-sonnet-4-20250514",
    },
    {
        "id": "prov_openai",
        "name": "openai",
        "enabled": 0,
        "base_url": "https://api.openai.com/v1",
        "api_key_env_var": "OPENAI_API_KEY",
        "priority": 30,
        "default_model": "gpt-4.1",
    },
    {
        "id": "prov_deepseek",
        "name": "deepseek",
        "enabled": 0,
        "base_url": "https://api.deepseek.com",
        "api_key_env_var": "DEEPSEEK_API_KEY",
        "priority": 40,
        "default_model": "deepseek-chat",
    },
]


async def _exec_script(conn: AsyncConnection, sql: str) -> None:
    # aiosqlite/SQLAlchemy executes one statement at a time more reliably
    for stmt in sql.split(";"):
        lines = [
            line
            for line in stmt.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        chunk = "\n".join(lines).strip()
        if not chunk:
            continue
        await conn.execute(text(chunk))


async def _apply_migrations(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )
    )
    result = await conn.execute(text("SELECT version FROM schema_migrations"))
    applied = {row[0] for row in result.fetchall()}

    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for path in migrations:
        version = int(path.name.split("_", 1)[0])
        if version in applied:
            continue
        await _exec_script(conn, path.read_text(encoding="utf-8"))
        await conn.execute(
            text("INSERT INTO schema_migrations(version) VALUES (:v)"),
            {"v": version},
        )


async def _seed(conn: AsyncConnection) -> None:
    meta = await conn.execute(text("SELECT id FROM app_meta WHERE id = 1"))
    if meta.fetchone() is None:
        await conn.execute(
            text(
                """
                INSERT INTO app_meta(id, schema_version, install_id, app_version, created_at)
                VALUES (1, 1, :install_id, :app_version, :created_at)
                """
            ),
            {
                "install_id": str(uuid.uuid4()),
                "app_version": settings.app_version,
                "created_at": utc_now(),
            },
        )

    lic = await conn.execute(text("SELECT id FROM license_state WHERE id = 1"))
    if lic.fetchone() is None:
        await conn.execute(
            text(
                """
                INSERT INTO license_state(id, tier, status, features_json)
                VALUES (1, 'free', 'inactive', '[]')
                """
            )
        )

    for key, value in DEFAULT_SETTINGS.items():
        existing = await conn.execute(
            text("SELECT key FROM settings WHERE key = :key"), {"key": key}
        )
        if existing.fetchone() is None:
            await conn.execute(
                text(
                    """
                    INSERT INTO settings(key, value_json, updated_at)
                    VALUES (:key, :value_json, :updated_at)
                    """
                ),
                {
                    "key": key,
                    "value_json": json.dumps(value),
                    "updated_at": utc_now(),
                },
            )

    for prov in DEFAULT_PROVIDERS:
        existing = await conn.execute(
            text("SELECT id FROM llm_providers WHERE id = :id"), {"id": prov["id"]}
        )
        if existing.fetchone() is None:
            await conn.execute(
                text(
                    """
                    INSERT INTO llm_providers(
                        id, name, enabled, base_url, api_key_env_var,
                        priority, default_model, config_json
                    ) VALUES (
                        :id, :name, :enabled, :base_url, :api_key_env_var,
                        :priority, :default_model, '{}'
                    )
                    """
                ),
                prov,
            )


async def init_db(engine: AsyncEngine | None = None) -> None:
    engine = engine or get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys = ON"))
        await conn.execute(text("PRAGMA journal_mode = WAL"))
        await conn.execute(text("PRAGMA busy_timeout = 5000"))
        # Prefer migration file; fall back to schema.sql if migrations empty
        if any(MIGRATIONS_DIR.glob("*.sql")):
            await _apply_migrations(conn)
        else:
            await _exec_script(conn, SCHEMA_PATH.read_text(encoding="utf-8"))
        await _seed(conn)
