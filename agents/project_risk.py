"""Gate 0 — classificador de risco tecnológico vs modernização operacional.

Heurística determinística (sem LLM obrigatório) para bloquear falsos positivos
de subvenção quando o projeto é compra de equipamento pronto / ERP / obra.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

# Sinais de P&D / risco tecnológico real
_RD_POSITIVE = (
    r"\bp&d\b",
    r"\bpd&i\b",
    r"\bpesquisa\b",
    r"\bdesenvolvimento (de |tecnol)",
    r"\bco-desenvolvimento\b",
    r"\bprot[oó]tipo\b",
    r"\bprova de conceito\b",
    r"\bpoc\b",
    r"\bin[eé]dito\b",
    r"\bpatente\b",
    r"\btrl\s*[1-6]\b",
    r"\bincerteza (t[eé]cnica|cient[ií]fica)\b",
    r"\brisco tecnol[oó]gico\b",
    r"\balgoritmo (pr[oó]prio|novo|gen[eé]tico|de anti)\b",
    r"\bmodelo (matem[aá]tico|preditivo)\b",
    r"\bensaio (laboratorial|cl[ií]nico)\b",
    r"\bvalida[cç][aã]o experimental\b",
    r"\bscale-?up\b",
    r"\bprocesso inovador\b",
    r"\btecnologia pr[oó]pria\b",
    r"\bin vitro\b",
    r"\bin silico\b",
    r"\bs[ií]ntese (qu[ií]mica|de pept)",
    r"\bpermeabilidade\b",
    r"\bbarreira hematoencef[aá]lica\b",
    r"\bformula[cç][aã]o matem[aá]tica\b",
    r"\bcriptograf",
    r"\breticulados\b",
    r"\bcomputa[cç][aã]o qu[aâ]ntica\b",
    r"\bcatalisadores?\b",
    r"\beletroqu[ií]mic",
    r"\bnanopart[ií]cul",
)

# Sinais de modernização / aquisição pronta (sem P&D)
_MODERNIZATION = (
    r"\baquisi[cç][aã]o de (forno|m[aá]quina|equipamento|erp|sistema|software)\b",
    r"\bcompra de (forno|m[aá]quina|equipamento|erp|licen)\b",
    r"\bforno(s)? (combinado|importado|pronto)?\b",
    r"\bm[aá]quina(s)? pronta(s)?\b",
    r"\bequipamento(s)? (pronto|de prateleira|comercial)\b",
    r"\berp\b",
    r"\bsistema de gest[aã]o\b",
    r"\bsoftware de prateleira\b",
    r"\blicen[cç]a(s)? de software\b",
    r"\bsap\b",
    r"\btotvs\b",
    r"\bbling\b",
    r"\breforma (do |da )?(sal[aã]o|loja|infraestrutura)\b",
    r"\bampli[aã][cç][aã]o (da |do )?(loja|padaria|f[aá]brica|galp[aã]o)\b",
    r"\bmoderniza[cç][aã]o operacional\b",
    r"\bsubstitui[cç][aã]o de equipamento\b",
    r"\bimplanta[cç][aã]o de (erp|sistema|pdv)\b",
    r"\btrl\s*9\b",
    r"\bpronto para (o )?mercado\b",
    r"\bproduto acabado\b",
    r"\bplataforma pronta\b",
    r"\bplacas? solares?\b",
    r"\binstalar (placas|sistemas? solares?)\b",
    r"\bcontratar instaladores\b",
    r"\bcomprar equipamentos\b",
)

_RD_NEGATION = (
    r"n[aã]o se aplica a p&d",
    r"nao se aplica a p&d",
    r"sem (p&d|pd&i|risco tecnol)",
    r"n[aã]o h[aá] (p&d|risco tecnol)",
    r"n[aã]o apresenta adicionalidade",
    r"nao apresenta adicionalidade",
    r"nem evid[eê]ncia de desenvolvimento tecnol",
    r"sem (evid[eê]ncia de )?desenvolvimento tecnol",
    r"n[aã]o [eé] apresentado diferencial de inova",
)

# Rubricas tipicamente vedadas em subvenção econômica
_FORBIDDEN_BUDGET = (
    (
        r"(?:compra|aquisi[cç][aã]o)\s+(?:de\s+)?(?:im[oó]vel|terreno|lote)|"
        r"\bescrit[uó]rio comercial\b",
        "compra de imóvel/terreno",
    ),
    (r"\bobra(s)? civil|constru[cç][aã]o civil|reforma estrutural|alvenaria", "obras civis estruturais"),
    (r"\bve[ií]culo(s)? (administrativ|utilitári|passeio)|autom[oó]vel|caminhonete", "veículos administrativos"),
    (
        r"\bgoogle ads|meta ads|instagram ads|facebook ads|marketing digital|"
        r"\bmarketing\b|tr[aá]fego pago",
        "marketing comercial / ads",
    ),
    (r"\bpublicidade|propaganda comercial", "publicidade comercial"),
)

_VERTICAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "semiconductors": (
        "semicondutor",
        "semiconductor",
        "chip",
        "wafer",
        "fotolitograf",
        "microeletr",
    ),
    "energy_transition": (
        "hidrogênio",
        "hidrogenio",
        "hidrogênio verde",
        "transição energética",
        "transicao energetica",
        "eólica",
        "eolico",
        "fotovolta",
        "biocombust",
        "descarboniza",
    ),
    "audiovisual": ("audiovisual", "cinema", "produção cultural", "producao cultural", "streaming"),
    "agro": ("agro", "agricultura", "semente", "pecuária", "pecuaria"),
    "health": ("saúde", "saude", "farmac", "biotecnologia", "médic", "medic"),
}


@dataclass
class ProjectDiagnosis:
    """Resultado do Gate 0."""

    has_technological_risk: bool
    project_nature: str  # pd_i | modernization | mixed | unclear
    ineligible_budget_items: list[str] = field(default_factory=list)
    budget_math_inconsistency: bool = False
    budget_declared: float | None = None
    budget_sum_items: float | None = None
    inferred_trl: int | None = None
    signals_rd: list[str] = field(default_factory=list)
    signals_modernization: list[str] = field(default_factory=list)
    critical_alerts: list[str] = field(default_factory=list)
    redirect_suggestions: list[dict[str, str]] = field(default_factory=list)
    # Trilha do relatório (categoria → narrativa/UI distintas)
    report_track: str = "unclear"  # pd_i | modernization_credit | mixed | unclear
    report_track_label: str = "Perfil a confirmar"
    report_track_hint: str = ""
    primary_path: str = "avaliar"  # subvencao | credito | misto | avaliar

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_report_track(
    *,
    has_risk: bool,
    nature: str,
) -> tuple[str, str, str, str]:
    """Define a trilha do parecer: P&D vs modernização/crédito."""
    if has_risk and nature in {"pd_i", "mixed"}:
        return (
            "pd_i",
            "P&D / Inovação",
            "Perfil com risco tecnológico — priorize subvenção, chamada de pesquisa ou parceria de PD&I.",
            "subvencao",
        )
    if not has_risk or nature == "modernization":
        return (
            "modernization_credit",
            "Modernização / Crédito",
            "Sem enquadramento típico de subvenção P&D na base indexada — caminho tende a crédito/consultoria (orientação, não aprovação).",
            "credito",
        )
    if nature == "mixed":
        return (
            "mixed",
            "Perfil misto",
            "Há sinais de P&D e de modernização — compare subvenção elegível com crédito antes de decidir.",
            "misto",
        )
    return (
        "unclear",
        "Perfil a confirmar",
        "Sinais insuficientes — refine o dossiê ou escolha o caminho (P&D vs crédito) com a equipe.",
        "avaliar",
    )


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
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", cleaned):
        cleaned = cleaned.replace(",", "")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", cleaned):
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _find_patterns(text: str, patterns: Sequence[str]) -> list[str]:
    hits: list[str] = []
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            hits.append(m.group(0))
    return hits


def detect_forbidden_budget_items(text: str) -> list[str]:
    found: list[str] = []
    for pat, label in _FORBIDDEN_BUDGET:
        if re.search(pat, text, flags=re.IGNORECASE):
            found.append(label)
    return found


_TOTAL_KEY_RE = re.compile(
    r"^(total|valor\s*(total|solicitado|declarado)|or[cç]amento\s*total|"
    r"investimento\s*total|soma|subtotal)\b",
    flags=re.IGNORECASE,
)


def _is_total_label(label: str) -> bool:
    return bool(_TOTAL_KEY_RE.search((label or "").strip()))


def _money_with_unit(num: str, unit: str | None) -> float | None:
    n = _parse_money(num)
    if n is None:
        return None
    u = (unit or "").lower().strip()
    # "mi" / "milhão" / "milhões" → escala em milhões
    if u in {"mi", "mio"} or "milh" in u:
        return n * 1_000_000 if n < 10_000 else n
    if u == "mil" or u.startswith("mil "):
        return n * 1_000 if n < 10_000 else n
    return n


_NON_INVESTMENT_LABEL = re.compile(
    r"(custo\s+anual|economizar|economia|payback|faturamento|receita|"
    r"produ[cç][aã]o\s+m[eé]dia|demanda|baseline|meta\b|"
    r"[eé]\s+de\s+aproximadamente|aproxima)",
    flags=re.IGNORECASE,
)


def _is_investment_label(label: str) -> bool:
    key = (label or "").strip()
    if len(key) < 3 or _is_total_label(key):
        return False
    if _NON_INVESTMENT_LABEL.search(key):
        return False
    return True


def parse_budget_items_from_text(text: str) -> dict[str, float]:
    """Extrai rubricas de investimento do texto (ignora custo/economia operacional)."""
    items: dict[str, float] = {}
    blob = text or ""

    # 1) Linhas explícitas "Investimento previsto: R$ 12,6 milhões" (CAPEX por medida)
    inv_vals: list[float] = []
    for num, unit in re.findall(
        r"Investimento(?:\s+previsto)?\s*:\s*R\$\s*([\d.,]+)\s*"
        r"(milh[aã]o|milh[oõ]es|mi|mil)?",
        blob,
        flags=re.IGNORECASE,
    ):
        val = _money_with_unit(num, unit)
        if val is not None and val > 0:
            inv_vals.append(val)
    if len(inv_vals) >= 2:
        return {f"Investimento medida {i + 1}": v for i, v in enumerate(inv_vals)}

    # 2) "Pessoal R$ 1,8 milhao; equipamentos R$ 1,4 milhao; viagens R$ 900 mil"
    for name, num, unit in re.findall(
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ ]{2,24})\s*R\$\s*([\d.,]+)\s*"
        r"(milh[aã]o|milh[oõ]es|mi|mil)",
        blob,
        flags=re.IGNORECASE,
    ):
        key = name.strip()
        if not _is_investment_label(key):
            continue
        val = _money_with_unit(num, unit)
        if val is not None and val > 0:
            items[key] = val

    if len(items) >= 2:
        return items

    # 3) Tabela curta "Refrigeração R$ 12,6 mi" (sem verbo Investimento)
    for name, num, unit in re.findall(
        r"(?:^|\n)\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 /&\-]{2,40}?)\s+R\$\s*([\d.,]+)\s*"
        r"(milh[aã]o|milh[oõ]es|mi|mil)\b",
        blob,
        flags=re.IGNORECASE,
    ):
        key = name.strip(" :;-,\t")
        if not _is_investment_label(key) or len(key) > 40:
            continue
        val = _money_with_unit(num, unit)
        if val is not None and val > 0:
            items[key] = val

    if len(items) >= 2:
        return items

    # 4) Tabela "Nome\n2.350.000" (sem R$)
    for name, val in re.findall(
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 ,;&/\-]{3,60})\s*\n\s*([\d]{1,3}(?:\.\d{3}){1,3})\b",
        blob,
    ):
        key = name.strip()
        if key.lower() in {"categoria", "valor", "justificativa", "fase", "período", "periodo"}:
            continue
        if not _is_investment_label(key):
            continue
        items[key] = float(val.replace(".", ""))

    return items


def _line_item_values(items: dict[str, float] | list[Any]) -> list[float]:
    vals: list[float] = []
    if isinstance(items, dict):
        for k, v in items.items():
            if not _is_investment_label(str(k)):
                continue
            n = _parse_money(v)
            if n is not None and n > 0:
                vals.append(n)
        return vals
    for row in items:
        if isinstance(row, dict):
            label = str(row.get("name") or row.get("rubrica") or row.get("label") or "")
            if not _is_investment_label(label):
                continue
            n = _parse_money(row.get("value") or row.get("valor") or row.get("amount"))
        else:
            n = _parse_money(row)
        if n is not None and n > 0:
            vals.append(n)
    return vals


def sum_budget_line_items(
    form_data: dict[str, Any] | None,
    *,
    raw_text: str | None = None,
) -> tuple[float | None, bool]:
    """Soma rubricas de investimento; detecta inconsistência vs total declarado."""
    form = form_data or {}
    declared = _parse_money(form.get("budget_brl"))
    items = form.get("budget_items") or form.get("rubricas") or form.get("budget_breakdown")

    if not isinstance(items, (list, dict)):
        blob = "\n".join(
            str(x or "")
            for x in (
                raw_text,
                form.get("counterpart"),
                form.get("budget_detail"),
                form.get("summary"),
                form.get("methodology"),
            )
        )
        parsed = parse_budget_items_from_text(blob)
        items = parsed if parsed else None

    if not isinstance(items, (list, dict)):
        return declared, False

    vals = _line_item_values(items)
    if len(vals) < 2:
        return declared, False

    # Valores "mi" mal parseados (ex.: 12.6) com total em milhões → escala
    if declared and declared >= 100_000 and all(v < 1_000 for v in vals):
        vals = [v * 1_000_000 for v in vals]

    total = sum(vals)
    if declared is None:
        if raw_text:
            m = re.search(
                r"(?:investimento\s+total|total\s+declarado|valor\s+total|valor\s+solicitado|"
                r"TOTAL)\s*:?\s*R\$\s*([\d.,]+)\s*(milh[aã]o|milh[oõ]es|mi|mil)?",
                raw_text,
                flags=re.IGNORECASE,
            )
            if m:
                declared = _money_with_unit(m.group(1), m.group(2))
        if declared is None:
            return total, False

    # Se a soma estiver em ordem de grandeza absurda vs declarado, trata como ruído do parser
    if declared > 0 and (total > declared * 3 or total < declared * 0.2):
        return declared, False

    inconsistent = abs(total - declared) > max(1.0, declared * 0.05)
    return total, inconsistent


def build_redirect_suggestions(*, has_technological_risk: bool, uf: str | None = None) -> list[dict[str, str]]:
    if has_technological_risk:
        return []
    uf_u = (uf or "").upper()
    regional = {
        "PR": ("Fomento Paraná", "Linha estadual de crédito/fomento para modernização."),
        "RS": ("Badesul", "Crédito estadual para investimento produtivo."),
        "SP": ("Desenvolve SP", "Crédito e fomento estadual para empresas paulistas."),
        "SC": ("Badesc", "Crédito estadual para modernização."),
        "MG": ("BDMG", "Crédito estadual para investimento."),
    }
    suggestions = [
        {
            "name": "Sebraetec",
            "kind": "consultoria",
            "reason": (
                "Projeto de modernização operacional / aquisição pronta: "
                "Sebraetec apoia consultoria e implantação tecnológica sem exigir P&D."
            ),
        },
        {
            "name": "BNDES — crédito e financiamento (orientação)",
            "kind": "credito",
            "reason": (
                "Possível caminho de crédito — consultar o portal BNDES / agente financeiro. "
                "O SADS ainda não indexa linhas/programas BNDES (Finame, Mais Inovação etc.; em breve). "
                "Não é match de edital na base nem aprovação de financiamento."
            ),
        },
        {
            "name": "FINEP Inovacred (se houver inovação de processo)",
            "kind": "credito",
            "reason": (
                "Crédito reembolsável via agentes financeiros — só faça sentido se houver "
                "inovação de processo mensurável, não mera reposição de ativo."
            ),
        },
    ]
    if uf_u in regional:
        name, reason = regional[uf_u]
        suggestions.insert(
            1,
            {"name": name, "kind": "credito_estadual", "reason": reason},
        )
    return suggestions


def _is_system_notes(notes: str) -> bool:
    low = (notes or "").lower()
    return "preenchidos automaticamente" in low or "extraction_method" in low


def _quality_alerts(blob: str, form: dict[str, Any]) -> list[str]:
    """Sinais de dossiê incompleto / inconsistente (além de P&D e orçamento)."""
    alerts: list[str] = []
    # Cronograma vs duração — só quando o texto declara o conflito explicitamente
    m = re.search(
        r"fases?\s+somam\s+(\d+)\s*meses?.{0,120}?"
        r"dura[cç][aã]o\s+(?:declarada\s+)?(?:seja\s+de\s+|de\s+|é\s+|e\s+)?(\d+)\s*meses?",
        blob,
        flags=re.I | re.S,
    )
    if m:
        phases, declared = int(m.group(1)), int(m.group(2))
        if phases != declared:
            alerts.append(
                f"Cronograma inconsistente: fases somam {phases} meses, "
                f"mas a duração declarada é {declared} meses."
            )
    # Proposta rasa / sem definição
    shallow_hits = len(
        re.findall(
            r"n[aã]o (informa|define|h[aá]|foram definidos|enumera)|"
            r"propositalmente incompleto|dados simulados|proposta fict",
            blob,
            flags=re.I,
        )
    )
    if shallow_hits >= 3:
        alerts.append(
            "Dossiê insuficiente: faltam definições essenciais "
            "(método, escopo, baseline, equipe ou indicadores)."
        )
    return alerts


def diagnose_project(
    *,
    title: str,
    text: str,
    form_data: dict[str, Any] | None = None,
    trl: int | None = None,
    uf: str | None = None,
) -> ProjectDiagnosis:
    """Classifica risco tecnológico, rubricas vedadas e consistência orçamentária."""
    form = dict(form_data or {})
    notes = "" if _is_system_notes(str(form.get("notes") or "")) else str(form.get("notes") or "")

    # Se o formulário não trouxe rubricas, tenta extrair do PDF e persiste no form local
    if not form.get("budget_items"):
        parsed_items = parse_budget_items_from_text(text or "")
        if parsed_items:
            form["budget_items"] = parsed_items

    blob = " ".join(
        str(x or "")
        for x in (
            title,
            text,
            form.get("summary"),
            form.get("objectives"),
            form.get("methodology"),
            form.get("expected_results"),
            notes,
            form.get("counterpart"),
            " ".join(str(a) for a in (form.get("areas") or [])),
        )
    ).lower()

    negated_rd = any(re.search(p, blob, flags=re.IGNORECASE) for p in _RD_NEGATION)
    rd_hits = [] if negated_rd else _find_patterns(blob, _RD_POSITIVE)
    mod_hits = _find_patterns(blob, _MODERNIZATION)
    forbidden = detect_forbidden_budget_items(blob)
    sum_items, math_bad = sum_budget_line_items(form, raw_text=text)
    declared = _parse_money(form.get("budget_brl"))

    inferred_trl = trl
    if inferred_trl is None:
        m = re.search(r"trl\s*[=:]?\s*(\d{1,2})", blob, flags=re.IGNORECASE)
        if m:
            inferred_trl = int(m.group(1))

    # Decisão de risco tecnológico
    if negated_rd:
        has_risk = False
        nature = "modernization" if mod_hits else "unclear"
    elif inferred_trl is not None and inferred_trl >= 8 and not rd_hits:
        has_risk = False
        nature = "modernization"
    elif mod_hits and not rd_hits:
        has_risk = False
        nature = "modernization"
    elif rd_hits and not mod_hits:
        has_risk = True
        nature = "pd_i"
    elif rd_hits and mod_hits:
        # misto: risco se houver sinal forte de P&D (não só a palavra solta)
        strong_rd = any(
            re.search(p, blob, flags=re.IGNORECASE)
            for p in (
                r"\brisco tecnol",
                r"\bprot[oó]tipo\b",
                r"\bpatente\b",
                r"\bp&d\b",
                r"\bpd&i\b",
                r"\bin vitro\b",
                r"\bin silico\b",
                r"\bensaio cl[ií]nico\b",
                r"\balgoritmo",
                r"\bcriptograf",
            )
        )
        has_risk = strong_rd
        nature = "mixed"
    else:
        # sem sinais claros: não assume P&D (evita falso positivo de subvenção)
        has_risk = False
        nature = "unclear"

    alerts: list[str] = []
    if not has_risk:
        alerts.append(
            "Perfil de modernização/aquisição (sem P&D evidenciado): "
            "subvenção econômica não é o caminho. "
            "Não encaminhar como subvenção P&D: avalie crédito/consultoria/incentivo "
            "(orientação fora dos programas indexados do SADS)."
        )
    if forbidden:
        alerts.append(
            "Rubricas potencialmente vedadas em subvenção: " + "; ".join(forbidden) + "."
        )
    if math_bad:
        decl_s = f"R$ {declared:,.0f}".replace(",", ".") if declared else "não informado"
        sum_s = f"R$ {sum_items:,.0f}".replace(",", ".") if sum_items else "—"
        alerts.append(
            f"ORÇAMENTO NÃO BATE: soma das rubricas ({sum_s}) diverge do total declarado ({decl_s}). "
            "Não encaminhar até corrigir os números."
        )
    if inferred_trl is not None and inferred_trl >= 8 and not has_risk:
        alerts.append(
            f"TRL {inferred_trl} indica solução pronta/mercado — inadequado para linhas de P&D/subvenção."
        )
    alerts.extend(_quality_alerts(blob, form))

    track, track_label, track_hint, primary_path = _resolve_report_track(
        has_risk=has_risk, nature=nature
    )

    return ProjectDiagnosis(
        has_technological_risk=has_risk,
        project_nature=nature,
        ineligible_budget_items=forbidden,
        budget_math_inconsistency=math_bad,
        budget_declared=declared,
        budget_sum_items=sum_items if math_bad else None,
        inferred_trl=inferred_trl,
        signals_rd=rd_hits[:8],
        signals_modernization=mod_hits[:8],
        critical_alerts=alerts,
        redirect_suggestions=build_redirect_suggestions(
            has_technological_risk=has_risk, uf=uf
        ),
        report_track=track,
        report_track_label=track_label,
        report_track_hint=track_hint,
        primary_path=primary_path,
    )


def detect_vertical_mismatch(
    *,
    project_text: str,
    project_areas: Sequence[str],
    edict_title: str,
    edict_areas: Sequence[str],
) -> tuple[bool, str]:
    """True se o TÍTULO do edital é vertical restrito e o projeto não pertence a ele.

    Áreas genéricas sozinhas (ex.: tag "Saude" em edital amplo) não disparam o gate —
    evita falso negativo em sobreposição temática legítima.
    """
    title_l = (edict_title or "").lower()
    # reforço: área só conta se o título também sinalizar o vertical
    areas_l = " ".join(edict_areas or []).lower()
    project_blob = (" ".join([project_text, *project_areas])).lower()

    for vertical, keys in _VERTICAL_KEYWORDS.items():
        title_hit = any(k in title_l for k in keys)
        if not title_hit:
            continue
        # título vertical confirmado; áreas do edital só enriquecem o rótulo
        _ = areas_l
        project_hit = any(k in project_blob for k in keys)
        if not project_hit:
            return True, f"Edital vertical '{vertical}' incompatível com o setor do projeto"
    return False, ""
