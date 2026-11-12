"""Agente Avaliador (Scoring) — matriz v2 + hard gates de elegibilidade."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Sequence

from agents.instruments import (
    CompanyContext,
    INSTRUMENT_LABELS,
    build_comparison_note,
    build_company_context,
    build_improvements,
    build_why_this,
    infer_instrument,
    plain_instrument,
    score_instrument_fit,
)
from agents.project_risk import ProjectDiagnosis, detect_vertical_mismatch, diagnose_project
from agents.retrieval_agent import CompanyProfile, EdictMatch, ProjectQuery, RetrievalAgent

# Matriz v2+ : fit estruturado + instrumento contextual + semantico
W_SIMILARITY = 0.22
W_AREA = 0.20
W_TRL = 0.12
W_SIZE = 0.12
W_REGION = 0.08
W_BUDGET = 0.06
W_INSTRUMENT = 0.20

SCORE_WEIGHTS: dict[str, float] = {
    "similarity": W_SIMILARITY,
    "area": W_AREA,
    "trl": W_TRL,
    "size": W_SIZE,
    "region": W_REGION,
    "budget": W_BUDGET,
    "instrument": W_INSTRUMENT,
}

# Hard caps / kill switches
HARD_CAP_BLOCKED = 15.0
HARD_MULT_BLOCKED = 0.15
MIN_RECOMMEND_SCORE = 60.0
MPE_SIZES = {"MEI", "ME", "EPP"}
MPE_AGENCY_HINTS = ("centelha", "tecnova", "startup")
SUBVENCAO_LIKE = {"subvencao", "pesquisa"}

# ADR-009: BNDES só como orientação ampla — nunca linha/produto do catálogo legado.
BNDES_PORTAL_URL = (
    "https://www.bndes.gov.br/wps/portal/site/home/financiamento/navegador/"
)
BNDES_BROAD_IDS = frozenset({"bndes-credito-institucional"})


def _is_orientation_external_id(external_id: str | None) -> bool:
    eid = (external_id or "").strip().lower()
    return eid.startswith("redirect-") or eid in BNDES_BROAD_IDS


def _is_bndes_catalog_product(match: EdictMatch) -> bool:
    """True para editais BNDES indexados (legado) — excluir do ranking (ADR-009).

    Não usa o texto “Mais Inovação” sozinho: existe programa FINEP com esse nome.
    """
    if _is_orientation_external_id(match.external_id):
        return False
    agency = (match.agency or "").strip().upper()
    eid = (match.external_id or "").strip().lower()
    if agency == "BNDES":
        return True
    # IDs legados do coletor antigo (bndes-programa-..., bndes_finame_...).
    if eid.startswith("bndes-") or eid.startswith("bndes_"):
        return True
    return False


def _strip_bndes_catalog(matches: Sequence[EdictMatch]) -> list[EdictMatch]:
    return [m for m in matches if not _is_bndes_catalog_product(m)]


def _credit_matches_from_redirects(redirects: Sequence[dict[str, str]]) -> list[EdictMatch]:
    """Converte sugestões Gate 0 (crédito amplo/Sebraetec/estadual) em orientações (sem % de edital)."""
    out: list[EdictMatch] = []
    for i, sug in enumerate(redirects or []):
        name = str(sug.get("name") or "").strip()
        if not name:
            continue
        kind = str(sug.get("kind") or "").strip().lower()
        reason = str(sug.get("reason") or "").strip()
        low = f"{name} {kind} {reason}".lower()
        url = None
        if "sebraetec" in low or kind == "consultoria":
            instrument = "parceria"
            agency = "Sebrae"
        elif "bndes" in low:
            instrument = "credito"
            agency = "BNDES"
            url = BNDES_PORTAL_URL
            name = "BNDES — crédito e financiamento (orientação)"
            reason = (
                reason
                or (
                    "Possível caminho de crédito — consultar o portal BNDES / agente financeiro. "
                    "O SADS ainda não indexa linhas/programas BNDES (em breve). "
                    "Não é match de edital nem aprovação."
                )
            )
        elif "inovacred" in low or "credito" in kind:
            instrument = "credito"
            agency = "Fomento"
        else:
            instrument = "credito"
            agency = "Fomento"
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48] or f"redirect-{i}"
        # Similaridade baixa de propósito: orientação ≠ aderência a edital indexado.
        out.append(
            EdictMatch(
                external_id=f"redirect-{slug}",
                title=name,
                agency=agency,
                year=None,
                areas=["energia", "industria", "alimentos", "modernizacao", "credito"],
                url=url,
                distance=0.55,
                similarity=0.42,
                reasons=[reason] if reason else ["Orientação Gate 0 — fora da base indexada"],
                excerpt=reason,
                region="Todo Brasil",
                instrument=instrument,
                opportunity_type=kind or "credito",
            )
        )
    return out


@dataclass
class ScoreBreakdown:
    similarity: float  # 0-100
    area: float
    trl: float
    size: float
    region: float = 70.0
    budget: float = 70.0
    instrument: float = 55.0
    instrument_key: str = "outro"
    instrument_label: str = "Outro instrumento"
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
    eligibility_status: str = "ELEGÍVEL"
    block_reasons: list[str] = field(default_factory=list)
    why_this: str = ""
    comparison_note: str = ""
    improvements: list[str] = field(default_factory=list)
    instrument: str = "outro"
    context: dict[str, Any] = field(default_factory=dict)

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
            "eligibility_status": self.eligibility_status,
            "block_reasons": self.block_reasons,
            "breakdown": self.breakdown.to_dict(),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "summary": self.summary,
            "why_this": self.why_this,
            "comparison_note": self.comparison_note,
            "improvements": self.improvements,
            "instrument": self.instrument,
            "instrument_label": INSTRUMENT_LABELS.get(self.instrument, self.instrument),
            "context": self.context,
        }


@dataclass
class ScoringResult:
    project_title: str
    company_name: str
    reports: list[ScoreReport]
    context: dict[str, Any] = field(default_factory=dict)
    diagnosis: dict[str, Any] = field(default_factory=dict)
    recommended: list[ScoreReport] = field(default_factory=list)
    blocked: list[ScoreReport] = field(default_factory=list)
    redirect_suggestions: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_title": self.project_title,
            "company_name": self.company_name,
            "context": self.context,
            "diagnosis": self.diagnosis,
            "redirect_suggestions": self.redirect_suggestions,
            "reports": [r.to_dict() for r in self.reports],
            "recommended": [r.to_dict() for r in self.recommended],
            "blocked": [r.to_dict() for r in self.blocked],
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


def score_area(
    company_areas: Sequence[str],
    edict_areas: Sequence[str],
    *,
    project_text: str = "",
    edict_title: str = "",
) -> tuple[float, str]:
    """Fit temático — sem fallback generoso quando há vertical restrito incompatível."""
    mismatch, reason = detect_vertical_mismatch(
        project_text=project_text,
        project_areas=company_areas,
        edict_title=edict_title,
        edict_areas=edict_areas,
    )
    if mismatch:
        return 0.0, reason

    c = _norm_set(company_areas)
    e = _norm_set(edict_areas)
    if not e:
        return 40.0, "Edital sem areas/temas cadastrados (nota neutra-baixa)"
    if not c:
        return 25.0, "Empresa/projeto sem areas informadas"
    overlap = c & e
    if not overlap:
        soft = {a for a in c for b in e if a in b or b in a}
        if soft:
            return 55.0, f"Sobreposicao parcial de temas: {', '.join(sorted(soft))}"
        return 10.0, "Sem sobreposicao de areas/temas"
    ratio = len(overlap) / max(len(e), 1)
    points = 70.0 + 30.0 * min(1.0, ratio)
    return points, f"Sobreposicao de temas: {', '.join(sorted(overlap))}"


def score_trl(
    company_trl: int | None,
    edict_min_trl: int | None,
    *,
    instrument: str | None = None,
) -> tuple[float, str]:
    """TRL — subvenção/P&D não financia solução pronta (TRL >= 8)."""
    inst = (instrument or "").lower()
    if company_trl is not None and company_trl >= 8 and inst in SUBVENCAO_LIKE:
        return 5.0, (
            f"TRL {company_trl} (solução pronta/mercado) incompatível com "
            f"{plain_instrument(inst)} / P&D"
        )

    if edict_min_trl is None:
        if company_trl is not None and company_trl >= 8:
            return 35.0, f"TRL {company_trl} elevado; edital sem TRL minimo (nota cautelosa)"
        return 55.0, "Edital sem TRL minimo cadastrado (nota neutra)"
    if company_trl is None:
        return 40.0, "TRL do projeto/empresa nao informado"
    if company_trl >= edict_min_trl:
        # TRL muito acima do mínimo em subvenção pode indicar produto pronto
        if company_trl >= 8 and inst in SUBVENCAO_LIKE:
            return 10.0, f"TRL {company_trl} acima do perfil típico de subvenção/P&D"
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
    lowered = {s.lower() for s in sizes}
    if company_size.lower() in lowered:
        return 95.0, f"Porte {company_size} elegivel"
    return 0.0, f"Porte {company_size} fora de {', '.join(sizes)}"


def score_similarity(similarity: float) -> tuple[float, str]:
    points = max(0.0, min(100.0, float(similarity) * 100.0))
    return points, f"Similaridade cosseno={similarity:.3f} -> {points:.1f}/100"


def score_region(company_uf: str | None, edict_region: str | None) -> tuple[float, str]:
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
        if "todo brasil" in region_l or region_l in {"brasil", "nacional"} or "nacional" in region_l:
            return 90.0, f"Abrangencia nacional ({region})"
    if not uf:
        return 40.0, "UF da empresa nao informada"
    if uf.lower() in region_l or uf in region.upper():
        return 95.0, f"UF {uf} coberta pela regiao '{region}'"

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
        return 0.0, f"UF {uf} fora da regiao prioritaria '{region}'"

    # FAPESP / estadual explícito
    if "são paulo" in region_l or "sao paulo" in region_l or region_l.strip() in {"sp"}:
        if uf != "SP":
            return 0.0, f"Edital restrito a SP; empresa em {uf}"
        return 95.0, "UF SP coberta"

    if national:
        return 85.0, f"Abrangencia ampla ({region}); UF {uf} elegivel"
    return 40.0, f"Regiao '{region}' sem regra clara para UF {uf} (nota cautelosa)"


def score_budget(
    project_budget: float | None,
    budget_min: float | None = None,
    budget_max: float | None = None,
) -> tuple[float, str]:
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
    gap_ratio = (project_budget - hi) / max(hi, 1.0)
    points = max(10.0, 50.0 - 40.0 * min(1.0, gap_ratio))
    return points, f"Orcamento acima do maximo ({project_budget:,.0f} > {hi:,.0f})"


def score_deadline(prazo_proposta: str | None, *, now: datetime | None = None) -> tuple[float, str, bool]:
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


def _is_mpe_only_edict(title: str, agency: str | None, sizes: Sequence[str]) -> bool:
    blob = f"{agency or ''} {title}".lower()
    if any(h in blob for h in MPE_AGENCY_HINTS):
        return True
    if sizes and all(s.upper() in MPE_SIZES for s in sizes):
        return True
    return False


def _apply_hard_gates(
    *,
    total: float,
    inst: str,
    inst_pts: float,
    region_pts: float,
    size_pts: float,
    area_pts: float,
    trl_pts: float,
    deadline_ok: bool,
    deadline_detail: str,
    size_detail: str,
    region_detail: str,
    area_detail: str,
    trl_detail: str,
    inst_detail: str,
    diagnosis: ProjectDiagnosis | None,
    company: CompanyProfile,
    match: EdictMatch,
    edict_sizes: Sequence[str],
) -> tuple[float, bool, str, list[str]]:
    """Kill switches: retorna (score, eligible, status, block_reasons)."""
    blocks: list[str] = []
    status = "ELEGÍVEL"

    if not deadline_ok:
        blocks.append(f"❌ Bloqueado: Prazo encerrado — {deadline_detail}")

    # Instrumento / risco tecnológico
    if inst_pts <= 0.5:
        blocks.append(f"❌ Bloqueado: Fit de instrumento 0% — {inst_detail}")
    if diagnosis and not diagnosis.has_technological_risk and inst in SUBVENCAO_LIKE:
        blocks.append(
            "❌ Bloqueado: Exige Risco Tecnológico (P&D) — projeto classificado como modernização/aquisição"
        )

    # UF / região
    if region_pts <= 0.5:
        blocks.append(f"❌ Bloqueado: Restrito por região/UF — {region_detail}")

    # Porte / CNPJ / faturamento
    if size_pts <= 0.5 and edict_sizes:
        blocks.append(f"❌ Bloqueado: Exclusivo por porte — {size_detail}")

    revenue = getattr(company, "revenue_brl", None)
    size_n = (company.size or "").strip()
    size_u = size_n.upper()
    is_pf = size_u in {"PF", "PESSOA FISICA", "PESSOA FÍSICA"}
    if is_pf and inst in {"credito", "subvencao", "parceria"}:
        blocks.append(
            "❌ Bloqueado: Linha para PJ — proponente aparenta Pessoa Física (CPF), "
            "incompatível com financiamento/subvenção empresarial"
        )
    if _is_mpe_only_edict(match.title, match.agency, edict_sizes):
        if size_n in {"Grande", "Media", "Média"} or (revenue is not None and revenue > 4_800_000):
            blocks.append(
                "❌ Bloqueado: Exclusivo para MPE — faturamento/porte acima do limite típico "
                "(Centelha/Tecnova/startup)"
            )
        if is_pf:
            blocks.append("❌ Bloqueado: Exclusivo para MPE/PJ — proponente Pessoa Física")

    # Tema vertical
    if area_pts <= 0.5:
        blocks.append(f"❌ Bloqueado: Aderência temática incompatível — {area_detail}")

    # TRL pronto + subvenção
    if trl_pts <= 10 and inst in SUBVENCAO_LIKE and company.trl is not None and company.trl >= 8:
        blocks.append(f"❌ Bloqueado: TRL de produto pronto vs subvenção/P&D — {trl_detail}")

    # Orçamento inconsistente / rubricas vedadas (kill switch operacional)
    if diagnosis and diagnosis.budget_math_inconsistency:
        decl = diagnosis.budget_declared
        summ = diagnosis.budget_sum_items
        detail = ""
        if decl is not None and summ is not None:
            detail = f" (soma R$ {summ:,.0f} ≠ total R$ {decl:,.0f})".replace(",", ".")
        blocks.append(
            "❌ Bloqueado: Orçamento inconsistente — soma das rubricas diverge do total declarado"
            + detail
        )
    if diagnosis and diagnosis.ineligible_budget_items and inst in SUBVENCAO_LIKE:
        blocks.append(
            "❌ Bloqueado: Rubricas tipicamente vedadas em subvenção — "
            + "; ".join(diagnosis.ineligible_budget_items)
        )

    if blocks:
        capped = min(total * HARD_MULT_BLOCKED, HARD_CAP_BLOCKED)
        # Motivo principal no status
        if any("Orçamento inconsistente" in b for b in blocks):
            status = "INELEGÍVEL POR ORÇAMENTO"
        elif any("Rubricas tipicamente vedadas" in b for b in blocks):
            status = "INELEGÍVEL POR RUBRICAS"
        elif any("Risco Tecnológico" in b for b in blocks):
            status = "INELEGÍVEL / BLOQUEADO"
        elif any("região" in b.lower() or "UF" in b for b in blocks):
            status = "INELEGÍVEL POR REGIÃO"
        elif any("porte" in b.lower() or "MPE" in b or "PJ" in b for b in blocks):
            status = "INELEGÍVEL POR PORTE/CNPJ"
        elif any("temática" in b.lower() or "vertical" in b.lower() for b in blocks):
            status = "INELEGÍVEL POR TEMA"
        elif any("TRL" in b for b in blocks):
            status = "INELEGÍVEL POR TRL"
        elif any("Prazo" in b for b in blocks):
            status = "INELEGÍVEL POR PRAZO"
        else:
            status = "INELEGÍVEL / BLOQUEADO"
        return round(max(0.0, capped), 1), False, status, blocks

    return round(max(0.0, min(100.0, total)), 1), True, status, blocks


def compose_score(
    *,
    company: CompanyProfile,
    match: EdictMatch,
    project: ProjectQuery | None = None,
    context: CompanyContext | None = None,
    diagnosis: ProjectDiagnosis | None = None,
    edict_min_trl: int | None = None,
    edict_sizes: Sequence[str] | None = None,
    edict_region: str | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    prazo_proposta: str | None = None,
    instrument: str | None = None,
    opportunity_type: str | None = None,
) -> ScoreReport:
    """Calcula score composto 0-100 + hard gates + feedback."""
    project_budget = _parse_money(getattr(project, "budget_brl", None) if project else None)
    project_text = getattr(project, "text", "") if project else ""
    region = edict_region if edict_region is not None else getattr(match, "region", None)
    prazo = prazo_proposta if prazo_proposta is not None else getattr(match, "prazo_proposta", None)
    sizes = list(edict_sizes or [])

    ctx = context or build_company_context(
        size=company.size,
        project_budget=project_budget,
        revenue_brl=getattr(company, "revenue_brl", None),
        goal_preference=getattr(company, "goal_preference", None),
    )

    inst = instrument or getattr(match, "instrument", None) or infer_instrument(
        agency=match.agency,
        title=match.title,
        opportunity_type=opportunity_type or getattr(match, "opportunity_type", None),
    )

    if diagnosis is None and project is not None:
        diagnosis = diagnose_project(
            title=project.title,
            text=project_text,
            form_data=getattr(project, "form_data", None) or {},
            trl=company.trl,
            uf=company.uf,
        )

    sim_pts, sim_detail = score_similarity(match.similarity)
    area_pts, area_detail = score_area(
        company.areas,
        match.areas,
        project_text=project_text,
        edict_title=match.title,
    )
    trl_pts, trl_detail = score_trl(company.trl, edict_min_trl, instrument=inst)
    size_pts, size_detail = score_size(company.size, sizes)
    region_pts, region_detail = score_region(getattr(company, "uf", None), region)
    budget_pts, budget_detail = score_budget(project_budget, budget_min, budget_max)
    inst_pts, inst_detail = score_instrument_fit(inst, ctx)

    # Sem risco tecnológico: forçar instrument_fit ~0 em subvenção
    if diagnosis and not diagnosis.has_technological_risk and inst in SUBVENCAO_LIKE:
        inst_pts = 0.0
        inst_detail = (
            "Subvenção/P&D exige risco tecnológico; projeto classificado como modernização"
        )

    _deadline_pts, deadline_detail, deadline_ok = score_deadline(prazo)

    total = (
        sim_pts * W_SIMILARITY
        + area_pts * W_AREA
        + trl_pts * W_TRL
        + size_pts * W_SIZE
        + region_pts * W_REGION
        + budget_pts * W_BUDGET
        + inst_pts * W_INSTRUMENT
    )

    total, eligible, status, block_reasons = _apply_hard_gates(
        total=total,
        inst=inst,
        inst_pts=inst_pts,
        region_pts=region_pts,
        size_pts=size_pts,
        area_pts=area_pts,
        trl_pts=trl_pts,
        deadline_ok=deadline_ok,
        deadline_detail=deadline_detail,
        size_detail=size_detail,
        region_detail=region_detail,
        area_detail=area_detail,
        trl_detail=trl_detail,
        inst_detail=inst_detail,
        diagnosis=diagnosis,
        company=company,
        match=match,
        edict_sizes=sizes,
    )

    eligibility_flags = list(block_reasons)
    if not deadline_ok:
        pass
    elif _deadline_pts <= 55:
        eligibility_flags.append(deadline_detail)

    strengths: list[str] = []
    weaknesses: list[str] = []

    def _bucket(points: float, ok_msg: str, weak_msg: str) -> None:
        if points >= 70:
            strengths.append(ok_msg)
        elif points <= 45:
            weaknesses.append(weak_msg)
        else:
            strengths.append(ok_msg) if points >= 60 else weaknesses.append(weak_msg)

    _bucket(inst_pts, inst_detail, inst_detail)
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

    for br in block_reasons:
        if br not in weaknesses:
            weaknesses.insert(0, br)

    why = build_why_this(
        title=match.title,
        instrument=inst,
        context=ctx,
        instrument_pts=inst_pts,
        strengths=strengths,
        eligible=eligible,
    )
    if not eligible and block_reasons:
        why = (
            f"“{match.title}” foi bloqueado por hard gate de elegibilidade. "
            + " ".join(block_reasons[:2])
        )
    improvements = build_improvements(weaknesses)
    if diagnosis and not diagnosis.has_technological_risk:
        improvements.insert(
            0,
            "Se o objetivo é modernização (ERP/equipamentos), a base do SADS pode não ter "
            "edital adequado: trate crédito/consultoria como orientação, não como aprovação.",
        )

    orientation = _is_orientation_external_id(match.external_id)
    if orientation and eligible:
        why = (
            "Não há match com programa indexado na base do SADS (piloto FINEP/FAPESP). "
            "Possível caminho de crédito/consultoria — consultar portal oficial / agente. "
            "Linhas BNDES específicas ainda não estão no SADS (em breve). "
            "Isto não é aderência a edital nem aprovação."
        )
        strengths = [
            "Orientação de caminho (fora da base indexada)",
            "Consultar portal BNDES / agente financeiro — sem linha específica no SADS",
            "Separar orientação de match FINEP/FAPESP indexado",
        ]
        weaknesses = [
            "Sem edital BNDES indexado no corpus do SADS",
            "Não use percentual interno como aprovação de crédito",
        ]

    if not eligible:
        summary = why
    elif orientation:
        summary = why
    elif total >= 75:
        summary = why
    elif total >= 50:
        summary = why + " Há lacunas a corrigir antes de submeter."
    else:
        summary = why + " Considere outro instrumento ou ajuste o perfil do projeto."

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
            instrument=round(inst_pts, 1),
            instrument_key=inst,
            instrument_label=plain_instrument(inst),
        ),
        strengths=strengths,
        weaknesses=weaknesses,
        summary=summary,
        similarity=match.similarity,
        url=match.url,
        eligible=eligible,
        eligibility_flags=eligibility_flags,
        eligibility_status=status,
        block_reasons=block_reasons,
        why_this=why,
        improvements=improvements,
        instrument=inst,
        context=ctx.to_dict(),
    )


class ScoringAgent:
    """Avalia matches do Retrieval com nota, hard gates e narrativa."""

    def score_matches(
        self,
        *,
        project: ProjectQuery,
        company: CompanyProfile,
        matches: list[EdictMatch],
        edict_meta: dict[str, dict[str, Any]] | None = None,
        revenue_brl: float | None = None,
        goal_preference: str | None = None,
        diagnosis: ProjectDiagnosis | None = None,
    ) -> ScoringResult:
        edict_meta = edict_meta or {}
        project_budget = _parse_money(getattr(project, "budget_brl", None))
        revenue = revenue_brl if revenue_brl is not None else getattr(company, "revenue_brl", None)
        goal = goal_preference if goal_preference is not None else getattr(company, "goal_preference", None)
        context = build_company_context(
            size=company.size,
            project_budget=project_budget,
            revenue_brl=float(revenue) if revenue is not None else None,
            goal_preference=goal,
        )

        diag = diagnosis or diagnose_project(
            title=project.title,
            text=project.text,
            form_data=getattr(project, "form_data", None) or {},
            trl=company.trl,
            uf=company.uf,
        )

        # Modernização sem P&D: não forçar subvenção — priorizar crédito (BNDES amplo / estadual)
        if not diag.has_technological_risk and (not goal or goal in {"auto", "", "none"}):
            context = replace(
                context,
                preferred_instruments=("credito", "parceria"),
                avoided_instruments=("subvencao", "pesquisa", "bolsa"),
                rationale=(
                    "Projeto de modernização/aquisição sem P&D evidenciado: "
                    "subvenção P&D não enquadra; orientação típica é crédito/consultoria "
                    "(fora dos programas indexados — não é aprovação BNDES)."
                ),
            )

        # ADR-009: nunca ranquear Finame / Mais Inovação / etc. do corpus legado.
        work_matches = _strip_bndes_catalog(matches)
        # Modernização sem P&D: se não sobrou crédito indexado (FINEP/outros), injeta
        # orientações Gate 0 (BNDES portal amplo, Sebraetec…) — sem % de “linha aprovada”.
        if not diag.has_technological_risk:
            has_indexed_credit = any(
                (m.instrument or infer_instrument(agency=m.agency, title=m.title)) == "credito"
                and not _is_orientation_external_id(m.external_id)
                for m in work_matches
            )
            if not has_indexed_credit:
                work_matches.extend(_credit_matches_from_redirects(diag.redirect_suggestions))

        reports: list[ScoreReport] = []
        for match in work_matches:
            meta = edict_meta.get(match.external_id or "", {})
            instrument = meta.get("instrument") or getattr(match, "instrument", None)
            report = compose_score(
                company=company,
                match=match,
                project=project,
                context=context,
                diagnosis=diag,
                edict_min_trl=meta.get("min_trl", match.min_trl),
                edict_sizes=meta.get("company_sizes") or match.company_sizes or [],
                edict_region=meta.get("region", getattr(match, "region", None)),
                budget_min=_parse_money(meta.get("budget_min")),
                budget_max=_parse_money(meta.get("budget_max")),
                prazo_proposta=meta.get("prazo_proposta", getattr(match, "prazo_proposta", None)),
                instrument=instrument,
                opportunity_type=meta.get("opportunity_type") or getattr(match, "opportunity_type", None),
            )
            reports.append(report)

        reports.sort(key=lambda r: (r.eligible, r.score), reverse=True)

        recommended = [r for r in reports if r.eligible and r.score >= MIN_RECOMMEND_SCORE]
        blocked = [r for r in reports if not r.eligible]

        # Modernização: se ainda não há elegível de crédito, promove redirects como recomendação
        if not diag.has_technological_risk and not any(r.instrument == "credito" for r in recommended):
            for match in _credit_matches_from_redirects(diag.redirect_suggestions):
                if any(r.external_id == match.external_id for r in reports):
                    continue
                report = compose_score(
                    company=company,
                    match=match,
                    project=project,
                    context=context,
                    diagnosis=diag,
                    instrument=match.instrument,
                )
                reports.append(report)
            reports.sort(key=lambda r: (r.eligible, r.score), reverse=True)
            recommended = [r for r in reports if r.eligible and r.score >= MIN_RECOMMEND_SCORE]
            blocked = [r for r in reports if not r.eligible]

        # Narrativa comparativa só entre elegíveis
        pool = recommended or [r for r in reports if r.eligible] or reports
        if len(pool) >= 2:
            top, second = pool[0], pool[1]
            note = build_comparison_note(
                top_title=top.title,
                top_instrument=top.instrument,
                other_title=second.title,
                other_instrument=second.instrument,
                context=context,
            )
            top.comparison_note = note
            second.comparison_note = (
                f"Fica atrás de “{top.title}” no seu contexto atual. {note}"
            )

        ctx_dict = context.to_dict()
        ctx_dict["diagnosis"] = diag.to_dict()

        return ScoringResult(
            project_title=project.title,
            company_name=company.name,
            reports=reports,
            context=ctx_dict,
            diagnosis=diag.to_dict(),
            recommended=recommended,
            blocked=blocked,
            redirect_suggestions=list(diag.redirect_suggestions),
        )

    async def score_from_retrieval(
        self,
        project: ProjectQuery,
        company: CompanyProfile,
        *,
        k: int = 5,
        agency: str | None = None,
    ) -> ScoringResult:
        retrieval = RetrievalAgent()
        result = await retrieval.retrieve(project, company, k=k, agency=agency)
        return self.score_matches(project=project, company=company, matches=result.matches)
