"""Agente Avaliador (Scoring) — T-040.

Simula uma banca simplificada: nota 0-100, breakdown por criterio e feedback
de forcas/fraquezas (heuristico + similaridade do Retrieval).

Matriz v2 (consultoria): similaridade apenas desempatadora; fit estruturado
(tema, TRL, porte, regiao, orcamento) concentra 70% do peso.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence

from agents.retrieval_agent import CompanyProfile, EdictMatch, ProjectQuery, RetrievalAgent


# Matriz v2 — soma 1.0 (fit estruturado 70% + semantico 30%)
W_SIMILARITY = 0.30
W_AREA = 0.25
W_TRL = 0.15
W_SIZE = 0.15
W_REGION = 0.10
W_BUDGET = 0.05

SCORE_WEIGHTS: dict[str, float] = {
    "similarity": W_SIMILARITY,
    "area": W_AREA,
    "trl": W_TRL,
    "size": W_SIZE,
    "region": W_REGION,
    "budget": W_BUDGET,
}


@dataclass
class ScoreBreakdown:
    similarity: float  # 0-100
    area: float
    trl: float
    size: float
    region: float = 70.0
    budget: float = 70.0
    weights: dict[str, float] = field(default_factory=lambda: dict(SCORE_WEIGHTS))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScoreReport:
    external_id: str | None
    title: str
    agency: str | None
    score: float  # 0-100
    breakdown: ScoreBreakdown
    strengths: list[str]
    weaknesses: list[str]
    summary: str
    similarity: float
    url: str | None = None
    eligible: bool = True
    eligibility_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "external_id": self.external_id,
            "title": self.title,
            "agency": self.agency,
            "url": self.url,
            "score": self.score,
            "similarity": self.similarity,
            "eligible": self.eligible,
            "eligibility_flags": self.eligibility_flags,
            "breakdown": self.breakdown.to_dict(),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "summary": self.summary,
        }


@dataclass
class ScoringResult:
    project_title: str
    company_name: str
    reports: list[ScoreReport]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_title": self.project_title,
            "company_name": self.company_name,
            "reports": [r.to_dict() for r in self.reports],
            "weights": dict(SCORE_WEIGHTS),
        }


def _norm_set(values: Sequence[str]) -> set[str]:
    return {v.strip().lower() for v in values if v and v.strip()}


def _parse_money(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    # "R$ 1.200.000,50" ou "1200000"
    cleaned = re.sub(r"[^\d,.\-]", "", text)
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def score_area(company_areas: Sequence[str], edict_areas: Sequence[str]) -> tuple[float, str]:
    """Retorna (0-100, detalhe)."""
    c = _norm_set(company_areas)
    e = _norm_set(edict_areas)
    if not e:
        return 60.0, "Edital sem areas/temas cadastrados (nota neutra)"
    if not c:
        return 40.0, "Empresa/projeto sem areas informadas"
    overlap = c & e
    if not overlap:
        soft = {a for a in c for b in e if a in b or b in a}
        if soft:
            return 75.0, f"Sobreposicao parcial de temas: {', '.join(sorted(soft))}"
        return 25.0, "Sem sobreposicao de areas/temas"
    ratio = len(overlap) / max(len(e), 1)
    points = 70.0 + 30.0 * min(1.0, ratio)
    return points, f"Sobreposicao de temas: {', '.join(sorted(overlap))}"


def score_trl(company_trl: int | None, edict_min_trl: int | None) -> tuple[float, str]:
    if edict_min_trl is None:
        return 70.0, "Edital sem TRL minimo cadastrado (nota neutra-alta)"
    if company_trl is None:
        return 40.0, "TRL do projeto/empresa nao informado"
    if company_trl >= edict_min_trl:
        bonus = min(20.0, 5.0 * (company_trl - edict_min_trl))
        return 80.0 + bonus, f"TRL {company_trl} atende minimo {edict_min_trl}"
    gap = edict_min_trl - company_trl
    points = max(10.0, 55.0 - 10.0 * gap)
    return points, f"TRL {company_trl} abaixo do minimo {edict_min_trl} (gap={gap})"


def score_size(company_size: str | None, edict_sizes: Sequence[str]) -> tuple[float, str]:
    sizes = [s.strip() for s in edict_sizes if s and s.strip()]
    if not sizes:
        return 70.0, "Edital sem restricao explicita de porte (nota neutra-alta)"
    if not company_size:
        return 40.0, "Porte da empresa nao informado"
    if company_size in sizes:
        return 95.0, f"Porte {company_size} elegivel"
    # match flexivel (EPP vs epp)
    lowered = {s.lower() for s in sizes}
    if company_size.lower() in lowered:
        return 95.0, f"Porte {company_size} elegivel"
    return 20.0, f"Porte {company_size} fora de {', '.join(sizes)}"


def score_similarity(similarity: float) -> tuple[float, str]:
    points = max(0.0, min(100.0, float(similarity) * 100.0))
    return points, f"Similaridade cosseno={similarity:.3f} -> {points:.1f}/100"


def score_region(company_uf: str | None, edict_region: str | None) -> tuple[float, str]:
    """Aderencia territorial empresa (UF) vs regiao do edital."""
    region = (edict_region or "").strip()
    uf = (company_uf or "").strip().upper()
    if not region:
        return 70.0, "Edital sem regiao cadastrada (nota neutra-alta)"
    region_l = region.lower()
    national = any(
        token in region_l
        for token in ("todo brasil", "nacional", "brasil", "todas as regioes", "nationwide")
    )
    if national and "norte" not in region_l and "nordeste" not in region_l:
        # "Todo Brasil" / Nacional
        if "todo brasil" in region_l or region_l in {"brasil", "nacional"} or "nacional" in region_l:
            return 90.0, f"Abrangencia nacional ({region})"
    if not uf:
        return 40.0, "UF da empresa nao informada"
    if uf.lower() in region_l or uf in region.upper():
        return 95.0, f"UF {uf} coberta pela regiao '{region}'"

    # macros regionais brasileiras (aproximacao)
    macro = {
        "N": {"AC", "AP", "AM", "PA", "RO", "RR", "TO"},
        "NE": {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"},
        "CO": {"DF", "GO", "MT", "MS"},
        "SE": {"ES", "MG", "RJ", "SP"},
        "S": {"PR", "RS", "SC"},
    }
    labels = {
        "N": ("norte",),
        "NE": ("nordeste",),
        "CO": ("centro-oeste", "centro oeste", "centrooeste"),
        "SE": ("sudeste",),
        "S": ("sul",),
    }
    matched_macros = []
    for key, words in labels.items():
        if any(w in region_l for w in words):
            matched_macros.append(key)
    if matched_macros:
        if any(uf in macro[m] for m in matched_macros):
            return 95.0, f"UF {uf} na regiao prioritaria '{region}'"
        return 20.0, f"UF {uf} fora da regiao prioritaria '{region}'"

    if national:
        return 85.0, f"Abrangencia ampla ({region}); UF {uf} elegivel"
    return 55.0, f"Regiao '{region}' sem regra clara para UF {uf} (nota intermedia)"


def score_budget(
    project_budget: float | None,
    budget_min: float | None = None,
    budget_max: float | None = None,
) -> tuple[float, str]:
    """Valor pedido do projeto vs faixa do edital (quando conhecida)."""
    if budget_min is None and budget_max is None:
        return 70.0, "Edital sem faixa de valor cadastrada (nota neutra-alta)"
    if project_budget is None:
        return 40.0, "Orcamento do projeto nao informado"
    lo = budget_min if budget_min is not None else 0.0
    hi = budget_max if budget_max is not None else float("inf")
    if lo <= project_budget <= hi:
        return 95.0, f"Orcamento {project_budget:,.0f} dentro da faixa do edital"
    if project_budget < lo:
        gap_ratio = (lo - project_budget) / max(lo, 1.0)
        points = max(15.0, 55.0 - 40.0 * min(1.0, gap_ratio))
        return points, f"Orcamento abaixo do minimo ({project_budget:,.0f} < {lo:,.0f})"
    # acima do max
    gap_ratio = (project_budget - hi) / max(hi, 1.0)
    points = max(10.0, 50.0 - 40.0 * min(1.0, gap_ratio))
    return points, f"Orcamento acima do maximo ({project_budget:,.0f} > {hi:,.0f})"


def score_deadline(prazo_proposta: str | None, *, now: datetime | None = None) -> tuple[float, str, bool]:
    """Soft score + flag de elegibilidade temporal (nao entra na matriz; usado em flags)."""
    if not prazo_proposta:
        return 70.0, "Prazo de proposta nao cadastrado", True
    raw = prazo_proposta.strip()
    try:
        if raw.endswith("Z"):
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return 60.0, f"Prazo nao parseavel ({raw})", True
    ref = now or datetime.now(timezone.utc)
    if dt < ref:
        return 5.0, f"Prazo de proposta encerrado em {dt.date().isoformat()}", False
    days = (dt - ref).days
    if days <= 7:
        return 55.0, f"Prazo critico: {days} dia(s) restantes ({dt.date().isoformat()})", True
    if days <= 30:
        return 75.0, f"Prazo util: {days} dias restantes ({dt.date().isoformat()})", True
    return 90.0, f"Prazo confortavel: {days} dias ({dt.date().isoformat()})", True


def compose_score(
    *,
    company: CompanyProfile,
    match: EdictMatch,
    project: ProjectQuery | None = None,
    edict_min_trl: int | None = None,
    edict_sizes: Sequence[str] | None = None,
    edict_region: str | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    prazo_proposta: str | None = None,
) -> ScoreReport:
    """Calcula score composto 0-100 + feedback (matriz v2)."""
    project_budget = _parse_money(getattr(project, "budget_brl", None) if project else None)
    region = edict_region if edict_region is not None else getattr(match, "region", None)
    prazo = prazo_proposta if prazo_proposta is not None else getattr(match, "prazo_proposta", None)

    sim_pts, sim_detail = score_similarity(match.similarity)
    area_pts, area_detail = score_area(company.areas, match.areas)
    trl_pts, trl_detail = score_trl(company.trl, edict_min_trl)
    size_pts, size_detail = score_size(company.size, edict_sizes or [])
    region_pts, region_detail = score_region(getattr(company, "uf", None), region)
    budget_pts, budget_detail = score_budget(project_budget, budget_min, budget_max)
    _deadline_pts, deadline_detail, deadline_ok = score_deadline(prazo)

    total = (
        sim_pts * W_SIMILARITY
        + area_pts * W_AREA
        + trl_pts * W_TRL
        + size_pts * W_SIZE
        + region_pts * W_REGION
        + budget_pts * W_BUDGET
    )

    eligibility_flags: list[str] = []
    if not deadline_ok:
        eligibility_flags.append(deadline_detail)
        total *= 0.35  # penalidade forte: prazo encerrado nao deve liderar ranking
    elif _deadline_pts <= 55:
        eligibility_flags.append(deadline_detail)

    # gates soft: porte/TRL claramente incompatíveis reduzem teto
    if size_pts <= 20 and edict_sizes:
        eligibility_flags.append(size_detail)
        total = min(total, 45.0)
    if trl_pts <= 25 and edict_min_trl is not None and company.trl is not None:
        eligibility_flags.append(trl_detail)
        total = min(total, 50.0)
    if region_pts <= 20:
        eligibility_flags.append(region_detail)
        total = min(total, 45.0)

    total = round(max(0.0, min(100.0, total)), 1)
    eligible = deadline_ok and size_pts > 20 and region_pts > 20

    strengths: list[str] = []
    weaknesses: list[str] = []

    def _bucket(points: float, ok_msg: str, weak_msg: str) -> None:
        if points >= 70:
            strengths.append(ok_msg)
        elif points <= 45:
            weaknesses.append(weak_msg)
        else:
            strengths.append(ok_msg) if points >= 60 else weaknesses.append(weak_msg)

    _bucket(sim_pts, f"Boa aderencia textual ({sim_detail})", f"Baixa aderencia textual ({sim_detail})")
    _bucket(area_pts, area_detail, area_detail)
    _bucket(trl_pts, trl_detail, trl_detail)
    _bucket(size_pts, size_detail, size_detail)
    _bucket(region_pts, region_detail, region_detail)
    _bucket(budget_pts, budget_detail, budget_detail)
    if not deadline_ok:
        weaknesses.append(deadline_detail)
    elif _deadline_pts >= 75:
        strengths.append(deadline_detail)
    else:
        weaknesses.append(deadline_detail)

    if not eligible:
        summary = (
            f"Aderencia BAIXA / risco de inelegibilidade ({total}/100) ao edital '{match.title}'. "
            "Ha bloqueios estruturais (prazo, porte, TRL ou regiao) — revise antes de priorizar."
        )
    elif total >= 75:
        summary = (
            f"Aderencia ALTA ({total}/100) ao edital '{match.title}'. "
            "Fit estruturado e semantico favoraveis; avance com revisao humana."
        )
    elif total >= 50:
        summary = (
            f"Aderencia MEDIA ({total}/100) ao edital '{match.title}'. "
            "Ha potencial, mas ha lacunas estruturais a corrigir antes de submeter."
        )
    else:
        summary = (
            f"Aderencia BAIXA ({total}/100) ao edital '{match.title}'. "
            "Considere outro edital ou ajuste profundo do projeto/perfil."
        )

    return ScoreReport(
        external_id=match.external_id,
        title=match.title,
        agency=match.agency,
        score=total,
        breakdown=ScoreBreakdown(
            similarity=round(sim_pts, 1),
            area=round(area_pts, 1),
            trl=round(trl_pts, 1),
            size=round(size_pts, 1),
            region=round(region_pts, 1),
            budget=round(budget_pts, 1),
        ),
        strengths=strengths,
        weaknesses=weaknesses,
        summary=summary,
        similarity=match.similarity,
        url=match.url,
        eligible=eligible,
        eligibility_flags=eligibility_flags,
    )


class ScoringAgent:
    """Avalia matches do Retrieval (ou lista EdictMatch) com nota e feedback."""

    def score_matches(
        self,
        *,
        project: ProjectQuery,
        company: CompanyProfile,
        matches: list[EdictMatch],
        edict_meta: dict[str, dict[str, Any]] | None = None,
    ) -> ScoringResult:
        edict_meta = edict_meta or {}
        reports: list[ScoreReport] = []
        for match in matches:
            meta = edict_meta.get(match.external_id or "", {})
            report = compose_score(
                company=company,
                match=match,
                project=project,
                edict_min_trl=meta.get("min_trl", match.min_trl),
                edict_sizes=meta.get("company_sizes") or match.company_sizes or [],
                edict_region=meta.get("region", getattr(match, "region", None)),
                budget_min=_parse_money(meta.get("budget_min")),
                budget_max=_parse_money(meta.get("budget_max")),
                prazo_proposta=meta.get("prazo_proposta", getattr(match, "prazo_proposta", None)),
            )
            reports.append(report)
        # elegiveis primeiro; depois nota
        reports.sort(key=lambda r: (r.eligible, r.score), reverse=True)
        return ScoringResult(
            project_title=project.title,
            company_name=company.name,
            reports=reports,
        )

    async def score_from_retrieval(
        self,
        project: ProjectQuery,
        company: CompanyProfile,
        *,
        k: int = 5,
        agency: str | None = None,
    ) -> ScoringResult:
        """Pipeline curto: Retrieval -> Scoring."""
        retrieval = RetrievalAgent()
        result = await retrieval.retrieve(project, company, k=k, agency=agency)
        return self.score_matches(project=project, company=company, matches=result.matches)
