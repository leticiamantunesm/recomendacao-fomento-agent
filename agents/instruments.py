"""Taxonomia de instrumentos de fomento + regra contextual porte/caixa/projeto."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal, Sequence

Instrument = Literal[
    "subvencao",
    "credito",
    "fiscal",
    "parceria",
    "bolsa",
    "pesquisa",
    "outro",
]

CashCapacity = Literal["baixa", "media", "alta"]
ProjectScale = Literal["pequeno", "medio", "grande"]

INSTRUMENT_LABELS: dict[str, str] = {
    "subvencao": "Subvenção / auxílio financeiro",
    "credito": "Crédito reembolsável",
    "fiscal": "Incentivo fiscal",
    "parceria": "Parceria de PD&I",
    "bolsa": "Bolsa / formação",
    "pesquisa": "Chamada de pesquisa",
    "outro": "Outro instrumento",
}


@dataclass
class CompanyContext:
    """Contexto econômico para preferir instrumento (não só elegibilidade formal)."""

    size: str | None = None
    cash_capacity: CashCapacity = "media"
    project_scale: ProjectScale = "medio"
    project_budget: float | None = None
    revenue_brl: float | None = None
    goal_preference: str | None = None  # auto | cash | fiscal | credito | parceria
    preferred_instruments: tuple[str, ...] = ()
    avoided_instruments: tuple[str, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "cash_capacity": self.cash_capacity,
            "project_scale": self.project_scale,
            "project_budget": self.project_budget,
            "revenue_brl": self.revenue_brl,
            "goal_preference": self.goal_preference or "auto",
            "preferred_instruments": list(self.preferred_instruments),
            "avoided_instruments": list(self.avoided_instruments),
            "rationale": self.rationale,
        }


def normalize_size(size: str | None) -> str | None:
    if not size:
        return None
    s = size.strip().upper()
    aliases = {
        "MICRO": "ME",
        "MICROEMPRESA": "ME",
        "PEQUENA": "EPP",
        "EPP": "EPP",
        "ME": "ME",
        "MEI": "MEI",
        "DEMAIS": "Grande",
        "GRANDE": "Grande",
        "MEDIA": "Media",
        "MÉDIA": "Media",
        "MEDIO": "Media",
        "MÉDIO": "Media",
    }
    if s in aliases:
        return aliases[s]
    for key, val in aliases.items():
        if key in s:
            return val
    return size.strip()


def infer_instrument(
    *,
    agency: str | None = None,
    title: str | None = None,
    opportunity_type: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Instrument:
    """Classifica o instrumento a partir da fonte/metadados/titulo."""
    meta = metadata or {}
    explicit = str(meta.get("instrument") or "").strip().lower()
    if explicit in INSTRUMENT_LABELS:
        return explicit  # type: ignore[return-value]

    blob = " ".join(
        str(x or "")
        for x in (
            agency,
            title,
            opportunity_type,
            meta.get("opportunity_type"),
            meta.get("notes"),
            " ".join(meta.get("themes") or []),
        )
    ).lower()

    agency_u = (agency or "").strip().upper()

    if agency_u == "BNDES" or "bndes" in blob or "financiamento" in blob or "crédito" in blob or "credito" in blob:
        return "credito"
    if agency_u == "EMBRAPII" or "embrapii" in blob or "unidade embrapii" in blob:
        return "parceria"
    if agency_u == "CENTELHA" or "centelha" in blob:
        return "subvencao"
    if "lei do bem" in blob or "incentivo fiscal" in blob or "isenção" in blob or "isencao" in blob or "irpj" in blob:
        return "fiscal"
    if "bolsa" in blob or "produtividade" in blob or "pq/" in blob or "bepe" in blob:
        return "bolsa"
    if agency_u == "FAPESP" and "pipe" not in blob:
        if "auxílio" in blob or "auxilio" in blob or "chamada" in blob:
            return "pesquisa"
    if "pipe" in blob or "subven" in blob or "fundo perdido" in blob or "não reembols" in blob or "nao reembols" in blob:
        return "subvencao"
    if agency_u in {"FINEP", "CNPQ"}:
        if "evento" in blob or "arc" in blob:
            return "pesquisa"
        return "subvencao"
    if agency_u == "FAPESP":
        return "subvencao" if "pipe" in blob else "pesquisa"
    return "outro"


def build_company_context(
    *,
    size: str | None,
    project_budget: float | None,
    revenue_brl: float | None = None,
    goal_preference: str | None = None,
) -> CompanyContext:
    """Deriva capacidade de caixa, escala do projeto e preferencia de instrumentos."""
    size_n = normalize_size(size)
    goal = (goal_preference or "auto").strip().lower()

    # Capacidade de caixa (proxy)
    if size_n in {"MEI", "ME"}:
        cash: CashCapacity = "baixa"
    elif size_n == "EPP":
        cash = "media"
    elif size_n in {"Media", "Grande"}:
        cash = "alta"
    else:
        cash = "media"
    if revenue_brl is not None:
        if revenue_brl < 360_000:
            cash = "baixa"
        elif revenue_brl < 4_800_000:
            cash = "media" if cash != "alta" else cash
        else:
            cash = "alta"

    # Escala do projeto no contexto da empresa
    scale: ProjectScale = "medio"
    if project_budget is None:
        scale = "medio"
    elif revenue_brl and revenue_brl > 0:
        ratio = project_budget / revenue_brl
        if ratio < 0.02:
            scale = "pequeno"
        elif ratio < 0.15:
            scale = "medio"
        else:
            scale = "grande"
    else:
        # Sem receita: usa porte + valor absoluto
        if cash == "alta" and project_budget < 1_000_000:
            scale = "pequeno"
        elif cash == "alta" and project_budget >= 5_000_000:
            scale = "grande"
        elif cash == "baixa" and project_budget >= 500_000:
            scale = "grande"
        elif cash == "baixa":
            scale = "medio"
        else:
            scale = "medio"

    preferred: list[str]
    avoided: list[str]
    rationale: str

    if goal in {"cash", "subvencao", "dinheiro"}:
        preferred, avoided = ["subvencao", "parceria"], ["fiscal", "credito"]
        rationale = "Objetivo declarado: priorizar recurso financeiro (subvenção/parceria)."
    elif goal in {"fiscal", "imposto", "isencao", "isenção"}:
        preferred, avoided = ["fiscal"], ["subvencao"]
        rationale = "Objetivo declarado: priorizar incentivo fiscal."
    elif goal in {"credito", "financiamento", "emprestimo"}:
        preferred, avoided = ["credito"], ["fiscal"]
        rationale = "Objetivo declarado: priorizar crédito reembolsável."
    elif goal in {"parceria", "embrapii"}:
        preferred, avoided = ["parceria", "subvencao"], ["fiscal"]
        rationale = "Objetivo declarado: priorizar parceria de PD&I."
    elif cash == "baixa":
        preferred, avoided = ["subvencao", "parceria", "bolsa"], ["fiscal", "credito"]
        rationale = (
            "Empresa com baixa capacidade de caixa: incentivo fiscal quase não ajuda "
            "(pouco IR a compensar). Priorize subvenção ou parceria que injete recurso no projeto."
        )
    elif cash == "alta" and scale == "pequeno":
        preferred, avoided = ["fiscal", "parceria"], ["subvencao"]
        rationale = (
            "Empresa com caixa e projeto pequeno no seu contexto: subvenção costuma ter "
            "custo burocrático alto demais. Incentivo fiscal ou parceria leve tendem a gerar mais valor."
        )
    elif cash == "alta" and scale == "grande":
        preferred, avoided = ["subvencao", "parceria", "credito"], ["bolsa"]
        rationale = (
            "Projeto grande frente ao porte: faz sentido compartilhar risco via subvenção, "
            "parceria Embrapii ou crédito direcionado — não só fiscal."
        )
    else:
        preferred, avoided = ["subvencao", "parceria", "fiscal"], ["bolsa"]
        rationale = (
            "Perfil intermediário: mantenha subvenção e parceria no radar; "
            "avalie fiscal se houver lucro tributável."
        )

    return CompanyContext(
        size=size_n,
        cash_capacity=cash,
        project_scale=scale,
        project_budget=project_budget,
        revenue_brl=revenue_brl,
        goal_preference=goal,
        preferred_instruments=tuple(preferred),
        avoided_instruments=tuple(avoided),
        rationale=rationale,
    )


def score_instrument_fit(
    instrument: str | None,
    context: CompanyContext,
) -> tuple[float, str]:
    """0-100: quão adequado o instrumento é para o contexto da empresa/projeto."""
    inst = (instrument or "outro").lower()
    label = INSTRUMENT_LABELS.get(inst, inst)

    if context.goal_preference and context.goal_preference not in {"auto", "", "none"}:
        if inst in context.preferred_instruments:
            return 95.0, f"{label} alinhado ao objetivo declarado"
        if inst in context.avoided_instruments:
            return 15.0, f"{label} desalinhado do objetivo declarado"
        return 55.0, f"{label} neutro frente ao objetivo declarado"

    if inst in context.preferred_instruments:
        if context.cash_capacity == "baixa" and inst == "subvencao":
            return 95.0, f"{label} é o encaixe típico para quem precisa de caixa no projeto"
        if context.cash_capacity == "alta" and context.project_scale == "pequeno" and inst == "fiscal":
            return 92.0, f"{label} costuma valer mais que subvenção quando há caixa e o projeto é pequeno"
        return 88.0, f"{label} adequado ao contexto ({context.cash_capacity}/{context.project_scale})"

    if inst in context.avoided_instruments:
        if context.cash_capacity == "baixa" and inst == "fiscal":
            return 12.0, "Incentivo fiscal pouco útil sem lucro/IR relevante para compensar"
        if context.cash_capacity == "alta" and context.project_scale == "pequeno" and inst == "subvencao":
            return 25.0, "Subvenção para projeto pequeno em empresa com caixa costuma ser pouco eficiente"
        if context.cash_capacity == "baixa" and inst == "credito":
            return 30.0, "Crédito exige capacidade de pagamento — risco alto sem caixa"
        return 28.0, f"{label} pouco adequado ao contexto atual"

    if inst == "pesquisa":
        return 60.0, f"{label}: útil se houver ICT/pesquisador; menos direto para execução empresarial"
    if inst == "bolsa":
        return 45.0, f"{label}: foca pessoa física/formação, não capital de projeto"
    return 55.0, f"{label}: encaixe intermediário"


def plain_instrument(instrument: str | None) -> str:
    return INSTRUMENT_LABELS.get((instrument or "outro").lower(), "instrumento de fomento")


def _scale_phrase(scale: ProjectScale) -> str:
    return {
        "pequeno": "de porte menor",
        "medio": "de porte intermediário",
        "grande": "de maior envergadura",
    }.get(scale, "do porte atual")


def _cash_phrase(cash: CashCapacity) -> str:
    return {
        "baixa": "com menor folga de caixa",
        "media": "com folga de caixa moderada",
        "alta": "com boa capacidade de aporte próprio",
    }.get(cash, "")


def build_why_this(
    *,
    title: str,
    instrument: str | None,
    context: CompanyContext,
    instrument_pts: float,
    strengths: Sequence[str],
    eligible: bool,
) -> str:
    """Justificativa executiva: por que este mecanismo é (ou não) o melhor encaminhamento."""
    label = plain_instrument(instrument)
    top_strength = next((s for s in strengths if s), None)
    profile = f"{_cash_phrase(context.cash_capacity)} e projeto {_scale_phrase(context.project_scale)}"
    if not eligible:
        return (
            f"“{title}” ({label}) não deve ser encaminhado sem revisão: "
            f"há risco concreto de inelegibilidade (porte, prazo ou tipo de proponente). "
            f"Confirme as regras oficiais antes de qualquer aprovação."
        )
    if instrument_pts >= 80:
        base = (
            f"Recomendamos encaminhar para “{title}” ({label}): "
            f"é o mecanismo mais aderente ao perfil da empresa ({profile})."
        )
    elif instrument_pts <= 35:
        base = (
            f"“{title}” ({label}) tem alguma proximidade temática, "
            f"mas não é o melhor mecanismo para uma empresa {profile}. "
            f"Use só se as alternativas melhores estiverem indisponíveis."
        )
    else:
        base = (
            f"“{title}” ({label}) é uma opção viável para o perfil atual "
            f"({profile}), embora não seja o encaixe ideal."
        )
    if top_strength:
        return f"{base} Motivo principal: {top_strength}."
    return base


def build_comparison_note(
    *,
    top_title: str,
    top_instrument: str | None,
    other_title: str,
    other_instrument: str | None,
    context: CompanyContext,
) -> str:
    """Comparação executiva entre a opção #1 e uma alternativa."""
    a = plain_instrument(top_instrument)
    b = plain_instrument(other_instrument)
    if (top_instrument or "") == (other_instrument or ""):
        return (
            f"“{top_title}” e “{other_title}” são do mesmo tipo ({a}). "
            f"A escolha entre elas depende de prazo, tema e elegibilidade formal no edital."
        )
    if context.cash_capacity == "baixa":
        return (
            f"Prefira “{top_title}” ({a}) a “{other_title}” ({b}): "
            f"com pouca folga de caixa, recurso não reembolsável no projeto "
            f"costuma ser mais seguro do que crédito ou benefício fiscal."
        )
    if context.cash_capacity == "alta" and context.project_scale == "pequeno":
        return (
            f"Prefira “{top_title}” ({a}) a “{other_title}” ({b}): "
            f"para projeto menor em empresa com boa capacidade de aporte, "
            f"incentivo fiscal ou parceria leve costuma render mais do que disputar subvenção."
        )
    return (
        f"“{top_title}” ({a}) encaixa melhor no perfil da empresa "
        f"do que “{other_title}” ({b})."
    )


def build_improvements(weaknesses: Sequence[str], *, max_items: int = 3) -> list[str]:
    """Converte fraquezas técnicas em ações simples para o usuário."""
    actions: list[str] = []
    for w in weaknesses:
        low = w.lower()
        if "porte" in low:
            actions.append("Confirme se o porte da empresa é aceito na chamada (ME/EPP/Demais).")
        elif "trl" in low:
            actions.append("Ajuste ou evidencie a maturidade tecnológica (TRL) exigida pelo edital.")
        elif "prazo" in low:
            actions.append("Verifique a data limite de submissão no site oficial antes de investir esforço.")
        elif "região" in low or "regiao" in low or "uf" in low:
            actions.append("Confira se a UF da empresa está na abrangência geográfica da chamada.")
        elif "orçamento" in low or "orcamento" in low:
            actions.append("Rebalanceie o orçamento do projeto para a faixa típica da chamada.")
        elif "área" in low or "area" in low or "tema" in low or "sobreposicao" in low or "sobreposição" in low:
            actions.append("Reforce no texto do projeto os temas/áreas exigidos pela chamada.")
        elif "fiscal" in low:
            actions.append("Se o objetivo for caixa imediato, priorize subvenção; fiscal só ajuda com lucro tributável.")
        elif "similaridade" in low or "aderencia textual" in low or "aderência textual" in low:
            actions.append("Reescreva o resumo destacando problema, solução, TRL e impacto mensurável.")
        else:
            actions.append(f"Tratar: {w}")
        if len(actions) >= max_items:
            break
    if not actions:
        actions.append("Revise anexos obrigatórios e elegibilidade do proponente no edital escolhido.")
    return actions[:max_items]


def enrich_edict_metadata(
    metadata: dict[str, Any] | None,
    *,
    agency: str | None,
    title: str | None,
) -> dict[str, Any]:
    """Garante instrument + rótulo no metadata do edital."""
    meta = dict(metadata or {})
    instrument = infer_instrument(
        agency=agency,
        title=title,
        opportunity_type=meta.get("opportunity_type"),
        metadata=meta,
    )
    meta["instrument"] = instrument
    meta["instrument_label"] = INSTRUMENT_LABELS[instrument]
    return meta
