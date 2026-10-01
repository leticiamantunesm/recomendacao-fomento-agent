"""Aplica scripts SQL de db/init no Neon/Postgres.

Uso:
  python -m scripts.migrate_db
"""

from __future__ import annotations

import asyncio
import re

from sqlalchemy import text

from app.config import ROOT_DIR, get_settings
from db.session import dispose_engine, get_engine, sanitize_async_database_url

INIT_DIR = ROOT_DIR / "db" / "init"


def _split_sql(sql: str) -> list[str]:
    """Split simples por ';' ignorando linhas de comentário --."""
    lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    parts = [p.strip() for p in cleaned.split(";")]
    return [p for p in parts if p]


async def apply_migrations() -> None:
    settings = get_settings()
    sanitize_async_database_url(settings.async_database_url)
    if "SUA_SENHA" in settings.database_url or "ep-XXXX" in settings.database_url:
        raise SystemExit(
            "DATABASE_URL ainda está com placeholder.\n"
            "Crie o arquivo .env (copy .env.example .env) e cole a URL real do Neon."
        )

    print(f"Host: {settings.database_host_hint}")

    engine = get_engine()
    sql_files = sorted(INIT_DIR.glob("*.sql"))
    if not sql_files:
        raise SystemExit(f"Nenhum .sql em {INIT_DIR}")

    async with engine.begin() as conn:
        for path in sql_files:
            print(f"Aplicando {path.relative_to(ROOT_DIR)} ...")
            statements = _split_sql(path.read_text(encoding="utf-8"))
            for stmt in statements:
                await conn.execute(text(stmt))
            print(f"  OK ({len(statements)} statements)")

        ext = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        print("extension vector:", ext.scalar_one_or_none())
        tables = await conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN (
                    'companies', 'projects', 'edicts',
                    'employees', 'documents', 'applications'
                  )
                ORDER BY table_name
                """
            )
        )
        print("tables:", [r[0] for r in tables.fetchall()])

    await dispose_engine()


def main() -> int:
    try:
        asyncio.run(apply_migrations())
    except SystemExit as exc:
        print(exc)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Falha na migração: {exc}")
        return 1
    print("migrate_db: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
