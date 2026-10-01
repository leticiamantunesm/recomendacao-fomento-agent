"""Testes do extrator de PDF (helpers)."""

from scripts.extract_pdfs import clean_text, slugify


def test_slugify_basic() -> None:
    assert slugify("Boletim-de-Inovacao-Fevereiro-02.2026.pdf").startswith("boletim")


def test_clean_text_collapses_blank_lines() -> None:
    raw = "a\n\n\n\nb  c"
    assert clean_text(raw) == "a\n\nb c"
