from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="METAAGENT_", extra="ignore")

    app_version: str = "0.1.0"
    db_path: Path = Path.home() / ".metaagent" / "studio.db"
    http_timeout_seconds: float = 30.0
    token_budget: int = 15000
    default_export_path: str = str(Path.home() / "MetaAgentExports")
    cors_origins: list[str] = ["*"]


settings = Settings()
