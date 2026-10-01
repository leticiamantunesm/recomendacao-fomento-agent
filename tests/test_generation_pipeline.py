"""Testes Generation + Orchestrator (T-041 / T-042) — sem rede."""

from agents.generation_agent import DraftRequest, GenerationAgent, _append_score_sections
from agents.scoring_agent import ScoreBreakdown, ScoreReport


def _report(**kwargs) -> ScoreReport:
    base = dict(
        external_id="finep-demo",
        title="Chamada Demo",
        agency="FINEP",
        score=82.5,
        breakdown=ScoreBreakdown(similarity=90.0, area=80.0, trl=70.0, size=95.0),
        strengths=["Boa aderencia textual"],
        weaknesses=["TRL abaixo do ideal"],
        summary="Aderencia ALTA (82.5/100).",
        similarity=0.9,
        url=None,
    )
    base.update(kwargs)
    return ScoreReport(**base)


def test_append_score_sections() -> None:
    draft = "# Rascunho\n\n## 6. Proximos passos\nok\n"
    out = _append_score_sections(draft, _report())
    assert "## 7. Avaliacao automatica" in out
    assert "82.5/100" in out
    assert "Boa aderencia textual" in out


def test_generation_agent_includes_scoring() -> None:
    agent = GenerationAgent()
    result = agent.draft(
        DraftRequest(
            project_title="Projeto X",
            project_text="Texto do projeto com inovacao digital e IA aplicada.",
            edict_title="Edital Y",
            edict_text="Chamada FINEP para inovacao e startups.",
            company_name="Empresa Demo",
            score_report=_report(),
        )
    )
    assert result.used_fallback or result.provider == "none"
    assert "## 7. Avaliacao automatica" in result.text
    assert "Empresa Demo" in result.text
