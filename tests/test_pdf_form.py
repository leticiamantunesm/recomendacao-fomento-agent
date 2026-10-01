"""Testes unitarios Fase A (sem Neon)."""

from app.cnpj_lookup import map_porte, normalize_cnpj
from app.pdf_form import guess_form_fields, guess_title


def test_guess_title() -> None:
    text = "Introducao\n\nPlataforma de Inovacao Digital para Industria\n\nConteudo..."
    assert "Plataforma" in guess_title(text)


def test_guess_form_fields_areas_and_budget() -> None:
    text = """
    Projeto de inovacao com inteligencia artificial.
    Objetivo: reduzir custos industriais com automacao.
    Metodologia
    Usaremos prototipos e validacao em campo.
    Resultados esperados
    Reducao de 20% no tempo de ciclo.
    Orcamento total R$ 1.200.000
    Duracao prevista: 18 meses
    """
    form = guess_form_fields(text, filename="demo.pdf")
    assert "trl" not in form
    assert any("inovacao" in a or "inteligencia" in a for a in form["areas"])
    assert form["budget_brl"]
    assert form["duration_months"] == 18
    assert form["extraction_ok"] is True
    assert "metodolog" in form["methodology"].lower() or "prototip" in form["methodology"].lower()


def test_normalize_cnpj() -> None:
    assert normalize_cnpj("12.345.678/0001-95") == "12345678000195"


def test_map_porte() -> None:
    assert map_porte("MICRO EMPRESA") == "ME"
    assert map_porte("EMPRESA DE PEQUENO PORTE") == "EPP"
    assert map_porte("DEMAIS") == "Demais"
    assert map_porte("MICROEMPREENDEDOR INDIVIDUAL") == "MEI"
    assert map_porte("ME") == "ME"

