"""Testes de helpers de migrate/seed (sem banco)."""

from scripts.migrate_db import _split_sql
from scripts.seed_corpus import _split_areas
from scripts.extract_pdfs import slugify


def test_split_sql_skips_comments() -> None:
    sql = """
    -- comment
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE IF NOT EXISTS companies (id UUID PRIMARY KEY);
    """
    parts = _split_sql(sql)
    assert len(parts) == 2
    assert "CREATE EXTENSION" in parts[0]
    assert "CREATE TABLE" in parts[1]


def test_split_areas() -> None:
    assert _split_areas("inovação;FINEP|agro") == ["inovação", "FINEP", "agro"]


def test_slug_matches_finep_extract_name() -> None:
    assert slugify("finep_1019381_EDITAL_-_ETAPA_NACIONAL.pdf").startswith("finep_1019381")
