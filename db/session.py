"""Conexão async com Neon/Postgres (SQLAlchemy + asyncpg)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def sanitize_async_database_url(url: str) -> str:
    """Converte para postgresql+asyncpg e remove params incompatíveis com asyncpg."""
    settings_url = url
    if settings_url.startswith("postgres://"):
        settings_url = "postgresql://" + settings_url[len("postgres://") :]
    if settings_url.startswith("postgresql://"):
        settings_url = "postgresql+asyncpg://" + settings_url[len("postgresql://") :]

    parsed = urlparse(settings_url)
    drop = {"channel_binding", "sslmode", "ssl"}
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in drop
    ]
    return urlunparse(parsed._replace(query=urlencode(query)))


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        url = sanitize_async_database_url(settings.async_database_url)
        _engine = create_async_engine(
            url,
            pool_pre_ping=True,
            connect_args={"ssl": True},
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
