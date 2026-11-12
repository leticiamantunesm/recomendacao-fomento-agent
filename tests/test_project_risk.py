"""Gate 0 — risco tecnológico vs modernização."""

from agents.project_risk import (
    diagnose_project,
    detect_forbidden_budget_items,
    detect_vertical_mismatch,
)
from agents.retrieval_agent import CompanyProfile, EdictMatch, ProjectQuery
from agents.scoring_agent import ScoringAgent, compose_score, score_trl


def test_bakery_modernization_has_no_tech_risk() -> None:
    diag = diagnose_project(
        title="Modernização da Padaria Pão Quente",
        text=(
            "Aquisição de fornos prontos e implantação de ERP de prateleira "
            "para gestão de estoque e PDV. TRL 9. Reforma da loja."
        ),
        form_data={"budget_brl": "180000", "trl": 9},
        trl=9,
        uf="PR",
    )
    assert diag.has_technological_risk is False
    assert diag.project_nature in {"modernization", "unclear"}
    assert diag.report_track == "modernization_credit"
    assert diag.primary_path == "credito"
    assert any("Sebraetec" in s["name"] for s in diag.redirect_suggestions)
    assert any("alerta" in a.lower() or "modernização" in a.lower() or "subvenção" in a.lower() or "crédito" in a.lower() or "credito" in a.lower() for a in diag.critical_alerts)


def test_rd_project_has_tech_risk() -> None:
    diag = diagnose_project(
        title="Novo sensor IoT com risco tecnológico",
        text=(
            "Desenvolvimento de protótipo inédito com P&D e validação experimental. "
            "Incerteza técnica na calibração. TRL 4. Patente em preparação."
        ),
        trl=4,
    )
    assert diag.has_technological_risk is True
    assert diag.project_nature in {"pd_i", "mixed"}
    assert diag.redirect_suggestions == []


def test_forbidden_budget_items() -> None:
    items = detect_forbidden_budget_items(
        "compra de terreno e obra civil estrutural mais google ads"
    )
    assert any("imóvel" in i or "terreno" in i for i in items)
    assert any("obra" in i for i in items)
    assert any("marketing" in i or "ads" in i for i in items)


def test_vertical_mismatch_semiconductor() -> None:
    bad, reason = detect_vertical_mismatch(
        project_text="padaria compra fornos e erp",
        project_areas=["comercio", "alimentos"],
        edict_title="FINEP Subvenção Semicondutores",
        edict_areas=["semicondutores", "microeletrônica"],
    )
    assert bad is True
    assert "vertical" in reason.lower() or "semiconduct" in reason.lower()


def test_trl_ready_vs_subvencao() -> None:
    pts, detail = score_trl(9, None, instrument="subvencao")
    assert pts <= 10
    assert "pront" in detail.lower() or "incompat" in detail.lower()


def test_bakery_blocks_finep_subvencao() -> None:
    company = CompanyProfile(
        name="Pão Quente",
        size="ME",
        trl=9,
        areas=["comercio", "alimentos"],
        uf="PR",
        revenue_brl=900_000,
    )
    project = ProjectQuery(
        title="Compra de fornos e ERP",
        text="Aquisição de fornos prontos e software de prateleira ERP. Modernização operacional. TRL 9.",
        budget_brl="200000",
        form_data={"trl": 9, "budget_brl": "200000"},
    )
    matches = [
        EdictMatch(
            external_id="finep-semi",
            title="FINEP Subvenção Econômica Semicondutores",
            agency="FINEP",
            year=2026,
            areas=["semicondutores"],
            url=None,
            distance=0.1,
            similarity=0.85,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="subvencao",
        ),
        EdictMatch(
            external_id="finep-energy",
            title="FINEP Transição Energética Hidrogênio Verde",
            agency="FINEP",
            year=2026,
            areas=["energia"],
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
        project=project, company=company, matches=matches
    )
    assert result.diagnosis["has_technological_risk"] is False
    # Subvenção FINEP deve permanecer bloqueada
    subs = [r for r in result.reports if r.instrument == "subvencao"]
    assert subs and all(not r.eligible for r in subs)
    assert all(r.score <= 15 for r in subs)
    # Modernização deve gerar recomendação de crédito/consultoria (não zerar o ranking)
    assert result.recommended, "deveria recomendar crédito/Sebraetec, não lista vazia"
    assert all(r.instrument != "subvencao" for r in result.recommended)
    assert any("Sebraetec" in s["name"] for s in result.redirect_suggestions)


def test_solar_excludes_bndes_catalog_and_uses_orientation() -> None:
    """ADR-009: Mais Inovação / linhas BNDES do corpus não viram #1 com % de 'aprovação'."""
    company = CompanyProfile(
        name="Solar Bairro",
        size="EPP",
        trl=9,
        areas=["energia"],
        uf="SP",
        revenue_brl=2_000_000,
    )
    project = ProjectQuery(
        title="SOLAR BAIRRO - Microgeracao Compartilhada",
        text=(
            "Instalacao de sistemas solares compartilhados com placas prontas. "
            "Modernizacao energeticamente eficiente sem P&D. TRL 9."
        ),
        budget_brl="1500000",
        form_data={"trl": 9, "budget_brl": "1500000"},
    )
    matches = [
        EdictMatch(
            external_id="bndes-programa-bndes-mais-inovacao-difusao-tecnologica",
            title="BNDES Mais Inovação - Difusão tecnológica (Indústria 4.0)",
            agency="BNDES",
            year=2025,
            areas=["energia", "inovacao"],
            url="https://www.bndes.gov.br/example",
            distance=0.15,
            similarity=0.82,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="credito",
        ),
        EdictMatch(
            external_id="finep-subvencao-pd",
            title="FINEP Subvenção Econômica Inovação",
            agency="FINEP",
            year=2026,
            areas=["inovacao"],
            url=None,
            distance=0.25,
            similarity=0.6,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="subvencao",
        ),
    ]
    result = ScoringAgent().score_matches(
        project=project, company=company, matches=matches
    )
    assert result.diagnosis["has_technological_risk"] is False
    assert not any(
        "Mais Inovação" in (r.title or "") or "mais-inovacao" in (r.external_id or "")
        for r in result.reports
    )
    assert result.recommended
    assert all(
        (r.external_id or "").startswith("redirect-") for r in result.recommended
    )
    top = result.recommended[0]
    summary_l = (top.summary or "").lower()
    assert "não é" in summary_l and "aprovação" in summary_l
    assert "portal" in summary_l or "orientação" in summary_l or "indexado" in summary_l


def test_rd_project_can_remain_eligible() -> None:
    company = CompanyProfile(
        name="DeepTech",
        size="EPP",
        trl=5,
        areas=["inovacao", "ia"],
        uf="SP",
    )
    project = ProjectQuery(
        title="Protótipo de visão computacional",
        text=(
            "P&D com risco tecnológico para protótipo inédito de visão computacional. "
            "Validação experimental em TRL 5."
        ),
        budget_brl="800000",
        form_data={"trl": 5},
    )
    report = compose_score(
        company=company,
        match=EdictMatch(
            external_id="finep-1",
            title="FINEP Subvenção Inovação Digital",
            agency="FINEP",
            year=2026,
            areas=["inovacao", "ia"],
            url=None,
            distance=0.1,
            similarity=0.9,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="subvencao",
        ),
        project=project,
        edict_min_trl=4,
        edict_sizes=["ME", "EPP"],
    )
    assert report.eligible is True
    assert report.score >= 60
    assert report.eligibility_status == "ELEGÍVEL"
