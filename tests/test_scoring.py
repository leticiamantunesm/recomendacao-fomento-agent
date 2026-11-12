"""Testes do Scoring Agent (T-040) — matriz v2."""

from agents.retrieval_agent import CompanyProfile, EdictMatch, ProjectQuery
from agents.scoring_agent import (
    SCORE_WEIGHTS,
    ScoringAgent,
    compose_score,
    score_area,
    score_budget,
    score_region,
    score_similarity,
    score_size,
    score_trl,
)


def _match(**kwargs) -> EdictMatch:
    base = dict(
        external_id="finep-1",
        title="Edital Demo",
        agency="FINEP",
        year=2026,
        areas=["inovacao"],
        url=None,
        distance=0.2,
        similarity=0.8,
        reasons=[],
        excerpt="",
        region="Todo Brasil",
    )
    base.update(kwargs)
    return EdictMatch(**base)


def test_weights_sum_to_one() -> None:
    assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9
    assert SCORE_WEIGHTS["similarity"] == 0.22
    assert SCORE_WEIGHTS["area"] == 0.20
    assert SCORE_WEIGHTS["instrument"] == 0.20


def test_score_similarity() -> None:
    pts, _ = score_similarity(0.8)
    assert abs(pts - 80.0) < 1e-6


def test_score_area_overlap() -> None:
    pts, detail = score_area(["inovacao", "IA"], ["Inovacao", "Saude"])
    assert pts >= 70
    assert "inovacao" in detail.lower()


def test_score_trl_gap() -> None:
    pts, _ = score_trl(3, 6)
    assert pts < 55


def test_score_size_ok() -> None:
    pts, _ = score_size("EPP", ["ME", "EPP"])
    assert pts >= 90


def test_score_region_macro() -> None:
    pts, _ = score_region("BA", "Nordeste e Norte")
    assert pts >= 90
    pts_bad, _ = score_region("SP", "Nordeste")
    assert pts_bad <= 25


def test_score_budget_in_range() -> None:
    pts, _ = score_budget(500_000, budget_min=100_000, budget_max=1_000_000)
    assert pts >= 90


def test_compose_score_high_fit() -> None:
    company = CompanyProfile(name="X", size="EPP", trl=6, areas=["inovacao"], uf="SP")
    project = ProjectQuery(
        title="P",
        text="P&D com risco tecnológico e protótipo inédito em validação experimental.",
        budget_brl="800000",
        form_data={"trl": 6},
    )
    report = compose_score(
        company=company,
        match=_match(
            similarity=0.9,
            areas=["inovacao"],
            region="Todo Brasil",
            instrument="subvencao",
            title="FINEP Subvenção Inovação",
        ),
        project=project,
        edict_min_trl=4,
        edict_sizes=["EPP"],
    )
    assert report.score >= 60
    assert report.breakdown.similarity >= 85
    assert report.breakdown.region >= 80
    assert report.eligible
    assert report.strengths


def test_scoring_agent_sorts_eligible_then_score() -> None:
    company = CompanyProfile(name="X", size="EPP", trl=5, areas=["inovacao"], uf="SP")
    project = ProjectQuery(
        title="P",
        text="P&D e desenvolvimento de protótipo com incerteza técnica.",
        form_data={"trl": 5},
    )
    matches = [
        _match(external_id="a", similarity=0.95, title="Alto sim inelegivel", region="Nordeste"),
        _match(external_id="b", similarity=0.7, title="Bom fit", region="Todo Brasil"),
    ]
    result = ScoringAgent().score_matches(project=project, company=company, matches=matches)
    # SP fora do Nordeste deve ficar atras de elegivel nacional
    assert result.reports[0].external_id == "b"
    assert result.reports[0].eligible is True
    assert result.reports[1].eligible is False
