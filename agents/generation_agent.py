"""Generation Agent (T-041) — rascunho RAG/template a partir de scoring + trechos."""

from __future__ import annotations

from dataclasses import dataclass

from agents.scoring_agent import ScoreReport
from app.llm import GenerationResult, get_llm_client, render_template_draft


@dataclass
class DraftRequest:
    project_title: str
    project_text: str
    edict_title: str
    edict_text: str
    company_name: str = "Empresa proponente"
    score_report: ScoreReport | None = None


class GenerationAgent:
    """Redige rascunho de aderencia projeto-edital (template/none por padrao)."""

    def __init__(self) -> None:
        self.llm = get_llm_client()

    def draft(self, req: DraftRequest) -> GenerationResult:
        extra = {
            "project_title": req.project_title,
            "edict_title": req.edict_title,
            "company_name": req.company_name,
        }
        if req.score_report is not None:
            # enriquecimento local alem do template base
            base = self.llm.generate(
                task="draft_submission",
                project_excerpt=req.project_text,
                edict_excerpt=req.edict_text,
                extra=extra,
            )
            enriched = _append_score_sections(base.text, req.score_report)
            return GenerationResult(
                text=enriched,
                provider=base.provider,
                used_fallback=base.used_fallback,
                notes=base.notes + "; +secoes de scoring",
            )

        return self.llm.generate(
            task="draft_submission",
            project_excerpt=req.project_text,
            edict_excerpt=req.edict_text,
            extra=extra,
        )

    def draft_from_score(
        self,
        *,
        company_name: str,
        project_title: str,
        project_text: str,
        edict_text: str,
        report: ScoreReport,
    ) -> GenerationResult:
        return self.draft(
            DraftRequest(
                project_title=project_title,
                project_text=project_text,
                edict_title=report.title,
                edict_text=edict_text,
                company_name=company_name,
                score_report=report,
            )
        )


def _append_score_sections(draft: str, report: ScoreReport) -> str:
    strengths = "\n".join(f"- {s}" for s in report.strengths) or "- (nenhum destaque automatico)"
    weaknesses = "\n".join(f"- {w}" for w in report.weaknesses) or "- (nenhuma lacuna automatica)"
    block = f"""

## 7. Avaliacao automatica (Scoring Agent)
- Nota composta: **{report.score:.1f}/100**
- Similaridade (30%): {report.breakdown.similarity}/100
- Tema/area (25%): {report.breakdown.area}/100
- TRL (15%): {report.breakdown.trl}/100
- Porte (15%): {report.breakdown.size}/100
- Regiao (10%): {report.breakdown.region}/100
- Orcamento (5%): {report.breakdown.budget}/100
- Elegivel: {"sim" if report.eligible else "nao / risco"}

### Forcas
{strengths}

### Fraquezas / lacunas
{weaknesses}

### Sintese
{report.summary}
"""
    # evita duplicar se ja existir
    if "## 7. Avaliacao automatica" in draft:
        return draft
    return draft.rstrip() + block + "\n"


def preview_template() -> str:
    return render_template_draft(
        project_excerpt="(exemplo)",
        edict_excerpt="(exemplo)",
        extra={"project_title": "Demo", "edict_title": "Edital", "company_name": "Empresa"},
    )
