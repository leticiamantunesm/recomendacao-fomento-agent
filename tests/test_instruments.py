"""Taxonomia de instrumento + regra contextual porte/caixa/projeto."""

from agents.instruments import (
    build_company_context,
    build_comparison_note,
    build_why_this,
    infer_instrument,
    score_instrument_fit,
)
from agents.retrieval_agent import CompanyProfile, EdictMatch, ProjectQuery
from agents.scoring_agent import SCORE_WEIGHTS, ScoringAgent


def test_infer_instrument_by_agency_and_title() -> None:
    assert infer_instrument(agency="BNDES", title="Financiamento inovacao") == "credito"
    assert infer_instrument(agency="EMBRAPII", title="Unidade Embrapii") == "parceria"
    assert infer_instrument(agency="CENTELHA", title="Centelha 3") == "subvencao"
    assert infer_instrument(agency="FINEP", title="Subvencao economica") == "subvencao"
    assert infer_instrument(agency="FAPESP", title="Auxilio Regular") == "pesquisa"
    assert infer_instrument(agency="FAPESP", title="PIPE Fase 1") == "subvencao"
    assert (
        infer_instrument(agency="MCTI", title="Lei do Bem - incentivo fiscal") == "fiscal"
    )


def test_startup_baixa_caixa_prefere_subvencao() -> None:
    ctx = build_company_context(size="ME", project_budget=400_000, revenue_brl=200_000)
    assert ctx.cash_capacity == "baixa"
    assert "subvencao" in ctx.preferred_instruments
    assert "fiscal" in ctx.avoided_instruments
    sub_pts, _ = score_instrument_fit("subvencao", ctx)
    fis_pts, _ = score_instrument_fit("fiscal", ctx)
    assert sub_pts >= 85
    assert fis_pts <= 25


def test_grande_caixa_projeto_pequeno_prefere_fiscal() -> None:
    ctx = build_company_context(
        size="Grande",
        project_budget=80_000,
        revenue_brl=50_000_000,
    )
    assert ctx.cash_capacity == "alta"
    assert ctx.project_scale == "pequeno"
    assert "fiscal" in ctx.preferred_instruments
    assert "subvencao" in ctx.avoided_instruments
    fis_pts, _ = score_instrument_fit("fiscal", ctx)
    sub_pts, _ = score_instrument_fit("subvencao", ctx)
    assert fis_pts >= 85
    assert sub_pts <= 35


def test_goal_preference_overrides_auto() -> None:
    ctx = build_company_context(
        size="Grande",
        project_budget=50_000,
        revenue_brl=80_000_000,
        goal_preference="cash",
    )
    assert "subvencao" in ctx.preferred_instruments
    pts, detail = score_instrument_fit("subvencao", ctx)
    assert pts >= 90
    assert "objetivo" in detail.lower()


def test_why_and_comparison_text() -> None:
    ctx = build_company_context(size="ME", project_budget=300_000)
    why = build_why_this(
        title="FINEP Subvencao",
        instrument="subvencao",
        context=ctx,
        instrument_pts=95,
        strengths=["Boa aderencia textual"],
        eligible=True,
    )
    assert "encaminhar" in why.lower() or "subven" in why.lower()
    note = build_comparison_note(
        top_title="FINEP Subvencao",
        top_instrument="subvencao",
        other_title="Lei do Bem",
        other_instrument="fiscal",
        context=ctx,
    )
    assert "FINEP" in note
    assert "Lei do Bem" in note


def test_scoring_ranks_subvencao_over_fiscal_for_startup() -> None:
    company = CompanyProfile(
        name="Startup",
        size="ME",
        trl=5,
        areas=["inovacao"],
        uf="SP",
        revenue_brl=180_000,
    )
    project = ProjectQuery(
        title="App",
        text="P&D de aplicativo inédito com protótipo e risco tecnológico. Inovacao digital TRL 5.",
        budget_brl="250000",
        form_data={"trl": 5},
    )
    matches = [
        EdictMatch(
            external_id="fiscal-1",
            title="Lei do Bem",
            agency="RFB",
            year=2026,
            areas=["inovacao"],
            url=None,
            distance=0.1,
            similarity=0.85,
            reasons=[],
            excerpt="",
            region="Todo Brasil",
            instrument="fiscal",
        ),
        EdictMatch(
            external_id="finep-sub",
            title="FINEP Subvencao Inovacao",
            agency="FINEP",
            year=2026,
            areas=["inovacao"],
            url=None,
            distance=0.15,
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
        revenue_brl=180_000,
    )
    assert result.reports[0].instrument == "subvencao"
    assert result.reports[0].why_this
    assert result.reports[0].comparison_note
    assert "subvencao" in result.context["preferred_instruments"]


def test_weights_include_instrument() -> None:
    assert "instrument" in SCORE_WEIGHTS
    assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9
    assert SCORE_WEIGHTS["instrument"] == 0.20
