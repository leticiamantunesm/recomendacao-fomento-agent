"""Testes unitários da Settings (T-003)."""

from app.config import Settings


def test_async_database_url_from_postgresql() -> None:
    s = Settings(
        DATABASE_URL="postgresql://user:pass@ep-x.sa-east-1.aws.neon.tech/neondb?sslmode=require"
    )
    assert s.async_database_url.startswith("postgresql+asyncpg://")
    assert "sslmode=require" in s.async_database_url
    assert "user:pass@" in s.async_database_url


def test_async_database_url_idempotent() -> None:
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/fomento"
    )
    assert s.async_database_url == "postgresql+asyncpg://user:pass@localhost:5432/fomento"


def test_database_host_hint_hides_password() -> None:
    s = Settings(
        DATABASE_URL="postgresql://neondb_owner:SECRET@ep-demo.neon.tech/neondb?sslmode=require"
    )
    assert s.database_host_hint == "ep-demo.neon.tech"
    assert "SECRET" not in s.database_host_hint
