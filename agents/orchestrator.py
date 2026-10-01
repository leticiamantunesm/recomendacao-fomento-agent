"""Orquestrador do pipeline de agentes (T-042).

Fluxo MVP:
  retrieve → score → generate → relatorio (markdown)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from agents.generation_agent import GenerationAgent
from agents.retrieval_agent import CompanyProfile, ProjectQuery, RetrievalAgent
from agents.scoring_agent import ScoringAgent
from app.config import ROOT_DIR, get_settings
from db.session import session_scope


@dataclass
class PipelineRequest:
    project_title: str
    project_text: str
    company_name: str = "Empresa Demo TCC"
    company_size: str | None = "EPP"
    company_trl: int | None = 5
    company_areas: list[str] = field(default_factory=lambda: ["inovacao", "tecnologias digitais"])
    agency: str | None = "FINEP"
    k: int = 5
    top_n_drafts: int = 1


@dataclass
class PipelineResult:
    request: dict[str, Any]
    retrieval: dict[str, Any]
    scoring: dict[str, Any]
    drafts: list[dict[str, Any]]
    report_path: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Orchestrator:
    """Encadeia Retrieval → Scoring → Generation e exporta relatorio."""

    def __init__(self) -> None:
        self.retrieval = RetrievalAgent()
        self.scoring = ScoringAgent()
        self.generation = GenerationAgent()
        self.settings = get_settings()

    async def run(self, req: PipelineRequest) -> PipelineResult:
        company = CompanyProfile(
            name=req.company_name,
            size=req.company_size,
            trl=req.company_trl,
            areas=list(req.company_areas),
        )
        project = ProjectQuery(title=req.project_title, text=req.project_text)

        retrieval_result = await self.retrieval.retrieve(
            project,
            company,
            k=req.k,
            agency=req.agency,
        )
        scoring_result = self.scoring.score_matches(
            project=project,
            company=company,
            matches=retrieval_result.matches,
        )

        drafts: list[dict[str, Any]] = []
        for report in scoring_result.reports[: max(1, req.top_n_drafts)]:
            edict_text = await self._load_edict_text(report.external_id)
            gen = self.generation.draft_from_score(
                company_name=req.company_name,
                project_title=req.project_title,
                project_text=req.project_text,
                edict_text=edict_text or report.title,
                report=report,
            )
            drafts.append(
                {
                    "external_id": report.external_id,
                    "edict_title": report.title,
                    "score": report.score,
                    "provider": gen.provider,
                    "used_fallback": gen.used_fallback,
                    "text": gen.text,
                }
            )

        created_at = datetime.now(timezone.utc).isoformat()
        report_path = self._write_report(
            req=req,
            retrieval=retrieval_result.to_dict(),
            scoring=scoring_result.to_dict(),
            drafts=drafts,
            created_at=created_at,
        )

        return PipelineResult(
            request={
                "project_title": req.project_title,
                "company_name": req.company_name,
                "company_size": req.company_size,
                "company_trl": req.company_trl,
                "company_areas": req.company_areas,
                "agency": req.agency,
                "k": req.k,
            },
            retrieval=retrieval_result.to_dict(),
            scoring=scoring_result.to_dict(),
            drafts=drafts,
            report_path=report_path,
            created_at=created_at,
        )

    async def _load_edict_text(self, external_id: str | None) -> str:
        if not external_id:
            return ""
        async with session_scope() as session:
            row = (
                await session.execute(
                    text(
                        """
                        SELECT left(raw_text, 6000) AS raw_text
                        FROM edicts
                        WHERE external_id = :eid
                        """
                    ),
                    {"eid": external_id},
                )
            ).mappings().first()
        # nao dispose aqui: orchestrator ainda pode usar sessao/engine depois
        return str((row or {}).get("raw_text") or "")

    def _write_report(
        self,
        *,
        req: PipelineRequest,
        retrieval: dict[str, Any],
        scoring: dict[str, Any],
        drafts: list[dict[str, Any]],
        created_at: str,
    ) -> str:
        out_dir = self.settings.outputs_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = out_dir / f"pipeline_report_{stamp}.md"

        lines = [
            "# Relatorio do pipeline de agentes",
            "",
            f"- Gerado em: `{created_at}`",
            f"- Projeto: **{req.project_title}**",
            f"- Empresa: **{req.company_name}** (porte={req.company_size}, TRL={req.company_trl})",
            f"- Filtro agency: `{req.agency}`",
            "",
            "## Ranking (Scoring)",
            "",
        ]
        for i, rep in enumerate(scoring.get("reports") or [], 1):
            lines.append(
                f"{i}. **{rep.get('score')}**/100 — `{rep.get('external_id')}` — {rep.get('title')}"
            )
            lines.append(f"   - {rep.get('summary')}")
        lines.append("")
        lines.append("## Rascunhos gerados")
        lines.append("")
        for d in drafts:
            lines.append(f"### {d.get('external_id')} (score={d.get('score')})")
            lines.append("")
            lines.append(d.get("text") or "")
            lines.append("")
        lines.append("---")
        lines.append("_Pipeline: Retrieval → Scoring → Generation (T-042)._")

        path.write_text("\n".join(lines), encoding="utf-8")
        try:
            return str(path.relative_to(ROOT_DIR))
        except ValueError:
            return str(path)
