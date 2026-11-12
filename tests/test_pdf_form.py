"""Testes unitarios Fase A (sem Neon)."""

from pathlib import Path

from app.cnpj_lookup import map_porte, normalize_cnpj
from app.pdf_form import guess_form_fields, guess_title, weak_fields
from scripts.extract_pdfs import extract_pdf

ROOT = Path(__file__).resolve().parents[1]
SEMENTE_PDF = ROOT / "docs" / "TCC" / "exemplos_projetos"


def test_guess_title() -> None:
    text = "Introducao\n\nPlataforma de Inovacao Digital para Industria\n\nConteudo..."
    assert "Plataforma" in guess_title(text)


def test_guess_form_fields_areas_and_budget() -> None:
    text = """
    Projeto de inovacao com inteligencia artificial.
    Objetivo: reduzir custos industriais com automacao.
    Metodologia
    Usaremos prototipos e validacao em campo com ensaios comparativos detalhados.
    Resultados esperados
    Reducao de 20% no tempo de ciclo e melhoria de qualidade industrial.
    Orcamento total R$ 1.200.000
    Duracao prevista: 18 meses
    """
    form = guess_form_fields(text, filename="demo.pdf")
    assert "trl" not in form
    assert any("inovação" in a or "inteligência" in a or "inovacao" in a for a in form["areas"])
    assert form["budget_brl"]
    assert form["duration_months"] == 18
    assert form["extraction_ok"] is True
    assert "prototip" in form["methodology"].lower() or "valida" in form["methodology"].lower()
    assert "confidence" in form
    assert form["extraction_method"] == "heuristic"


def test_summary_prefers_resumo_section() -> None:
    text = """
    Titulo Longo Do Projeto De Demonstracao

    Sumário
    1. Resumo · 2. Objetivos · 3. Metodologia

    1. Resumo
    Este projeto desenvolve sensores IoT para agricultura de precisao com foco em custo baixo
    e rastreabilidade de lotes em cooperativas familiares do semiárido.

    6. Objetivos
    Objetivo geral: validar prototipo em campo ate TRL 6 com indicadores de acuracia.

    7. Metodologia
    Ciclos de co-design, coleta de dados e validacao experimental com parceiros locais.
    """
    form = guess_form_fields(text, filename="demo.pdf")
    assert "sensores IoT" in form["summary"] or "agricultura" in form["summary"].lower()
    assert "Sumário" not in form["summary"] and "1. Resumo · 2" not in form["summary"]
    assert form["confidence"]["summary"] >= 0.4
    assert len(form["summary"]) >= 80


def test_semente_viva_heuristic_smoke() -> None:
    pdfs = list(SEMENTE_PDF.glob("*.pdf"))
    if not pdfs:
        return
    text, _pages, n_chars = extract_pdf(pdfs[0])
    assert n_chars > 1000
    form = guess_form_fields(text, filename=pdfs[0].name)
    assert form["extraction_ok"] is True
    assert "SEMENTE VIVA" in form["title"].upper()
    assert "estação portátil" in form["summary"].lower() or "semente viva" in form["summary"].lower()
    assert form["duration_months"] == 24
    assert form["budget_brl"]
    assert any("agro" in a.lower() or "visão" in a.lower() or "visao" in a.lower() for a in form["areas"])
    assert form["methodology"]
    # Não deve ser o PDF inteiro truncado no resumo.
    assert not form["summary"].lower().startswith("semente viva — plataforma")
    weak = weak_fields(form)
    # Heurística boa deve deixar poucos campos fracos.
    assert "summary" not in weak or form["confidence"]["summary"] >= 0.5


def test_normalize_cnpj() -> None:
    assert normalize_cnpj("12.345.678/0001-95") == "12345678000195"


def test_map_porte() -> None:
    assert map_porte("MICRO EMPRESA") == "ME"
    assert map_porte("EMPRESA DE PEQUENO PORTE") == "EPP"
    assert map_porte("DEMAIS") == "Demais"
    assert map_porte("MICROEMPREENDEDOR INDIVIDUAL") == "MEI"
    assert map_porte("ME") == "ME"
