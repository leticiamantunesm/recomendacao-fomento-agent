"""BUG_01 — Modernização energética (frigorífico): crédito/BNDES sem exigir P&D.

Caso real reportado na UI (nov/2026):
- Projeto Aurora (modernização energética, Vale Norte Alimentos, MG)
- SADS bloqueou TUDO por “sem P&D” + falso “orçamento não fecha”
- Só mostrou redirects textuais (Sebraetec/crédito), sem recomendar instrumento de crédito

Esperado correto:
- tech_risk = False (é modernização, não subvenção)
- NÃO inventar inconsistência orçamentária (total R$ 38,4 mi fecha)
- Bloquear subvenção FINEP
- RECOMENDAR instrumento de crédito (BNDES amplo / fomento)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from agents.project_risk import diagnose_project, parse_budget_items_from_text
from agents.retrieval_agent import CompanyProfile, EdictMatch, ProjectQuery
from agents.scoring_agent import ScoringAgent
from app.pdf_form import guess_form_fields

EXEMPLOS = Path(__file__).resolve().parents[1] / "docs" / "TCC" / "exemplos_projetos"
PDF = EXEMPLOS / "BUG_01_AURORA_FRIGORIFICO.pdf"

# Snapshot do comportamento ERRADO observado na UI (antes da correção)
OBSERVED_BUG = {
    "ui_recommended_count": 0,
    "ui_blocked_reason": "Fit de instrumento 0% / Exige Risco Tecnológico + Orçamento inconsistente",
    "ui_false_budget_sum": 44_500_038.4,
    "ui_declared_total": 38_400_000.0,
    "verdict": "FAIL",
    "notes": (
        "Gate de P&D e falso positivo de orçamento zeraram o ranking, "
        "incluindo linhas BNDES/crédito que NÃO exigem risco tecnológico."
    ),
}


@pytest.fixture(scope="module")
def aurora():
    if not PDF.exists():
        pytest.skip(f"PDF ausente: {PDF}")
    text = "\n".join((p.extract_text() or "") for p in PdfReader(str(PDF)).pages)
    form = guess_form_fields(text, PDF.name)
    diag = diagnose_project(
        title=form.get("title") or "Projeto Aurora",
        text=text,
        form_data=form,
        uf="MG",
    )
    company = CompanyProfile(
        name="Vale Norte Alimentos S.A.",
        size="Grande",
        trl=None,
        areas=["energia", "industria", "alimentos"],
        uf="MG",
        revenue_brl=200_000_000,
    )
    project = ProjectQuery(
        title=form.get("title") or "Projeto Aurora",
        text=text,
        budget_brl=form.get("budget_brl") or "38400000",
        form_data=form,
    )
    matches = [
        EdictMatch(
            external_id="bndes-credito-institucional",
            title="BNDES — Crédito e financiamento (consulta ao portal)",
            agency="BNDES",
            year=2026,
            areas=["energia", "industria"],
            url="https://www.bndes.gov.br/",
            distance=0.1,
            similarity=0.82,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="credito",
        ),
        EdictMatch(
            external_id="bdmg-credito",
            title="BDMG — Crédito para modernização industrial",
            agency="BDMG",
            year=2026,
            areas=["industria", "energia"],
            url=None,
            distance=0.15,
            similarity=0.78,
            reasons=[],
            excerpt="",
            region="MG",
            instrument="credito",
        ),
        EdictMatch(
            external_id="finep-sub-energia",
            title="FINEP Subvenção Inovação — Energia",
            agency="FINEP",
            year=2026,
            areas=["energia"],
            url=None,
            distance=0.12,
            similarity=0.8,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="subvencao",
        ),
    ]
    result = ScoringAgent().score_matches(
        project=project,
        company=company,
        matches=matches,
        diagnosis=diag,
        revenue_brl=200_000_000,
    )
    return {
        "text": text,
        "form": form,
        "diag": diag,
        "result": result,
        "bug_snapshot": OBSERVED_BUG,
    }


def test_bug_snapshot_documents_ui_failure(aurora):
    """Registra que a UI falhou neste caso (0 recomendações indevidas)."""
    snap = aurora["bug_snapshot"]
    assert snap["verdict"] == "FAIL"
    assert snap["ui_recommended_count"] == 0
    assert "P&D" in snap["ui_blocked_reason"] or "Risco" in snap["ui_blocked_reason"]


def test_aurora_is_modernization_not_rd(aurora):
    diag = aurora["diag"]
    assert diag.has_technological_risk is False
    assert diag.project_nature in {"modernization", "unclear", "mixed"}
    assert diag.report_track == "modernization_credit"
    assert "Crédito" in diag.report_track_label or "Modernização" in diag.report_track_label
    assert diag.primary_path == "credito"


def test_aurora_budget_should_not_false_flag(aurora):
    """Bug: parser somava custo anual/economia e lia '12,6 mi' como 12,6."""
    diag = aurora["diag"]
    items = parse_budget_items_from_text(aurora["text"])
    # Não deve misturar custo operacional / economia com CAPEX
    assert not any("custo anual" in k.lower() for k in items)
    assert not any("econom" in k.lower() for k in items)
    assert diag.budget_math_inconsistency is False, (
        f"Falso positivo de orçamento: declared={diag.budget_declared} "
        f"sum={diag.budget_sum_items} items={items}"
    )


def test_aurora_blocks_subvencao_but_recommends_credit(aurora):
    """Correção esperada: sem P&D bloqueia subvenção, mas NÃO zera crédito/BNDES."""
    result = aurora["result"]
    subs = [r for r in result.reports if r.instrument == "subvencao"]
    credits = [r for r in result.reports if r.instrument == "credito"]
    assert subs, "fixture deve incluir subvenção"
    assert credits, "fixture deve incluir crédito"
    assert all(not r.eligible for r in subs), "subvenção deve permanecer bloqueada sem P&D"
    assert any(r.eligible for r in credits), (
        "BUG: crédito/BNDES foi bloqueado junto com subvenção. "
        f"credits={[ (r.external_id, r.eligible, r.block_reasons[:1]) for r in credits ]}"
    )
    assert result.recommended, "deveria haver ao menos 1 recomendação de crédito"
    assert result.recommended[0].instrument == "credito"
    assert result.recommended[0].score >= 60


def test_aurora_injects_credit_when_retrieval_only_has_subvencao():
    """Simula a UI: corpus devolve só FINEP/FIP — motor deve injetar crédito amplo."""
    if not PDF.exists():
        pytest.skip(f"PDF ausente: {PDF}")
    text = "\n".join((p.extract_text() or "") for p in PdfReader(str(PDF)).pages)
    form = guess_form_fields(text, PDF.name)
    diag = diagnose_project(title="Aurora", text=text, form_data=form, uf="MG")
    company = CompanyProfile(
        name="Vale Norte",
        size="Grande",
        areas=["energia", "industria"],
        uf="MG",
        revenue_brl=200_000_000,
    )
    project = ProjectQuery(
        title="Aurora",
        text=text,
        budget_brl=form.get("budget_brl"),
        form_data=form,
    )
    only_sub = [
        EdictMatch(
            external_id="finep-sub",
            title="FINEP Subvenção Inovação",
            agency="FINEP",
            year=2026,
            areas=["energia"],
            url=None,
            distance=0.1,
            similarity=0.8,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="subvencao",
        ),
        EdictMatch(
            external_id="fip-bio",
            title="FIP Bioeconomia e Sustentabilidade",
            agency="FINEP",
            year=2026,
            areas=["bioeconomia"],
            url=None,
            distance=0.2,
            similarity=0.7,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="subvencao",
        ),
    ]
    result = ScoringAgent().score_matches(
        project=project,
        company=company,
        matches=only_sub,
        diagnosis=diag,
        revenue_brl=200_000_000,
    )
    assert all(not r.eligible for r in result.reports if r.instrument == "subvencao")
    assert result.recommended, "UI não pode ficar sem recomendação quando há crédito BNDES/fomento"
    assert any(
        r.instrument in {"credito", "parceria"} or (r.external_id or "").startswith("redirect-")
        for r in result.recommended
    )
