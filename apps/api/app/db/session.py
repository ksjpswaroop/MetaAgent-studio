from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite+aiosqlite:///{settings.db_path}"
        _engine = create_async_engine(url, connect_args={"check_same_thread": False})
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def async_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = async_session_factory()
    async with factory() as session:
        yield session


def reset_engine() -> None:
    """Test helper to force engine recreation."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
