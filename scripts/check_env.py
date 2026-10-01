"""Smoke check do ambiente Python (T-003).

Uso (com venv ativo):
  python -m scripts.check_env
"""

from __future__ import annotations

import importlib
import sys


REQUIRED_MODULES = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "asyncpg",
    "pydantic_settings",
    "httpx",
    "pypdf",
    "dotenv",
    "sentence_transformers",
]


def main() -> int:
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    failed: list[str] = []
    for name in REQUIRED_MODULES:
        try:
            mod = importlib.import_module(name)
            version = getattr(mod, "__version__", "?")
            print(f"  OK  {name} ({version})")
        except Exception as exc:  # noqa: BLE001 — smoke check deve listar qualquer falha
            failed.append(name)
            print(f"  FAIL {name}: {exc}")

    try:
        from app.config import get_settings

        settings = get_settings()
        print(f"  OK  settings database_host={settings.database_host_hint}")
        print(f"  OK  settings async_url_prefix={settings.async_database_url.split('://', 1)[0]}")
    except Exception as exc:  # noqa: BLE001
        failed.append("app.config")
        print(f"  FAIL app.config: {exc}")

    if failed:
        print(f"\nFalhou: {', '.join(failed)}")
        return 1

    print("\nT-003 smoke check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
