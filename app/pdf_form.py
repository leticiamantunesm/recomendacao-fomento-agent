"""Heurísticas para pré-preencher formulário de projeto a partir do PDF."""

from __future__ import annotations

import re
from typing import Any

# Próximo cabeçalho típico de proposta de fomento / TCC.
_NEXT_HEADER = (
    r"(?=\n\s*(?:\d+[\.\)]\s*)?(?:"
    r"resumo|abstract|sum[aá]rio\s+executivo|identifica[cç][aã]o|enquadramento|"
    r"contexto|solu[cç][aã]o|objetivo|metodolog|m[eé]todo|cronograma|equipe|"
    r"parceria|or[cç]amento|indicador|impacto|risco|comunica[cç][aã]o|"
    r"conformidade|resultado|anexo|justificativa|refer[eê]ncia|entreg"
    r")\b|\Z)"
)

_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": (
        r"resumo\s+executivo",
        r"sum[aá]rio\s+executivo",
        r"resumo",
        r"abstract",
        r"apresenta[cç][aã]o",
    ),
    "objectives": (
        r"objetivos?",
        r"objetivo\s+geral",
        r"objetivos?\s+espec[ií]ficos?",
        r"metas?",
    ),
    "methodology": (
        r"metodologia(?:\s+e\s+plano\s+de\s+p[,.]?\s*d\s*&\s*i)?",
        r"materiais?\s+e\s+m[eé]todos?",
        r"m[eé]todo",
        r"abordagem",
        r"procedimento",
    ),
    "expected_results": (
        r"resultados?\s+esperados?(?:[^\n]{0,60})?",
        r"resultados?\s+e\s+decis[aã]o",
        r"entreg[aá]veis?",
        r"produtos?\s+esperados?",
        r"impactos?\s+esperados?",
    ),
    "team": (
        r"equipe(?:\s+e\s+governan[cç]a)?",
        r"equipe\s+t[eé]cnica",
        r"recursos?\s+humanos?",
        r"coordena[cç][aã]o",
    ),
    "counterpart": (
        r"contrapartidas?",
        r"contrapartida\s+financeira",
        r"recursos?\s+pr[oó]prios?",
        r"cofinanciamento",
    ),
}

_AREA_TAXONOMY: list[tuple[str, tuple[str, ...]]] = [
    ("visão computacional", ("visão computacional", "visao computacional", "computer vision")),
    ("inteligência artificial", ("inteligência artificial", "inteligencia artificial", " machine learning", " aprendizado de máquina", "aprendizado de maquina")),
    ("agro", ("agricultura familiar", "agro", "agrícola", "agricola", "sementes", "agroneg")),
    ("inovação", ("inovação", "inovacao", "p,d&i", "p&d", "subvenção")),
    ("IoT", ("iot", "internet das coisas", "embarcad")),
    ("sustentabilidade", ("sustentab", "inclusão produtiva", "inclusao produtiva")),
    ("biotecnologia", ("biotecnologia", "biotech")),
    ("saúde", ("saúde", "saude", "health")),
    ("energia", ("energia", "renováveis", "renovaveis")),
    ("indústria 4.0", ("indústria 4.0", "industria 4.0")),
    ("digital", ("digital", "software", "aplicativo")),
    ("startup", ("startup", "scale-up")),
]

_PLACEHOLDER_OBJ = "Descrever objetivos alinhados ao edital (editar)."
_PLACEHOLDER_OBJ_EMPTY = "Descrever objetivos do projeto."


def guess_title(text: str, fallback: str = "Projeto sem titulo") -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    skip = (
        "página",
        "pagina",
        "confidential",
        "sumário",
        "sumario",
        "índice",
        "indice",
        "documento editável",
        "documento editavel",
        "proposta simulada",
        "dados integralmente",
    )
    # Junta título quebrado em várias linhas no topo (comum em pypdf).
    joined: list[str] = []
    for ln in lines[:12]:
        low = ln.lower()
        if any(s in low for s in skip):
            if joined:
                break
            continue
        if low.startswith("http") or re.match(r"^\d+\.\s", ln):
            if joined:
                break
            continue
        if len(ln) < 8:
            continue
        joined.append(ln)
        candidate = " ".join(joined)
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if 20 <= len(candidate) <= 220:
            # Para se a próxima linha parece metadado/seção.
            return candidate[:300]
        if len(candidate) > 220:
            return candidate[:300]
    if lines:
        return re.sub(r"\s+", " ", lines[0])[:300]
    return fallback[:300]


def _normalize_ws(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_tocish(chunk: str) -> bool:
    head = chunk[:220]
    if head.count("·") >= 2 or head.count("•") >= 3:
        return True
    # Vários "N. Titulo" colados no início = sumário.
    nums = re.findall(r"\b\d{1,2}\.\s+[A-ZÀ-Úa-z]", head)
    return len(nums) >= 3


def _section(blob: str, *header_patterns: str, max_chars: int = 1200) -> tuple[str, float]:
    """Retorna (texto, confiança) do melhor bloco após um cabeçalho."""
    best = ""
    best_score = -1.0
    for h in header_patterns:
        pat = rf"(?ims)^[ \t]*(?:\d+[\.\)]\s*)?{h}\s*[:\-–]?\s*(?:\n|\r\n)(.+?){_NEXT_HEADER}"
        for m in re.finditer(pat, blob):
            raw = m.group(1).strip()
            if _is_tocish(raw):
                continue
            chunk = re.sub(r"\s+", " ", raw).strip()
            if len(chunk) < 40:
                continue
            # Prefere blocos longos o bastante, mas não o documento inteiro.
            score = min(len(chunk), max_chars) / float(max_chars)
            if score > best_score:
                best_score = score
                best = chunk[:max_chars]
    if not best:
        return "", 0.0
    conf = 0.55 + 0.35 * best_score
    return best, min(conf, 0.95)


def _split_numbered_items(text: str) -> list[str]:
    """Quebra '1. foo 2. bar' ou bullets em itens separados."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?:(?<=\D)|^)\s*\d{1,2}[\.\)]\s+", text)
    items = [p.strip(" ;.-") for p in parts if len(p.strip(" ;.-")) >= 20]
    if len(items) >= 2:
        return items
    return []


def _objectives(blob: str) -> tuple[list[str], float]:
    found: list[str] = []
    section_text, sec_conf = _section(blob, *_SECTION_ALIASES["objectives"], max_chars=1600)

    search_space = section_text or blob
    # Objetivo geral (sem engolir a lista numerada).
    m = re.search(
        r"(?is)objetivo\s+geral\s*[:\-–]\s*(.+?)(?=\s+\d{1,2}[\.\)]\s+|objetivo\s+espec|metodolog|resultado|\Z)",
        search_space,
    )
    if m:
        line = re.sub(r"\s+", " ", m.group(1)).strip()[:500]
        if len(line) >= 20:
            found.append(line)

    numbered = _split_numbered_items(section_text or "")
    for item in numbered:
        if item.lower().startswith("objetivo geral"):
            continue
        if item not in found:
            found.append(item[:400])
        if len(found) >= 6:
            break

    if len(found) < 2:
        for pat in (
            r"(?m)^\s*(?:\d+[\.\)]\s+|[\-\*•]\s+)(.+)$",
            r"(?is)objetivos?\s+espec[ií]ficos?\s*[:\-–]?\s*(.+?)(?=metodolog|resultado|equipe|\Z)",
        ):
            for m in re.finditer(pat, section_text or ""):
                t = re.sub(r"\s+", " ", m.group(1)).strip()
                if 20 <= len(t) <= 320 and "objetivo geral" not in t.lower():
                    if t not in found:
                        found.append(t)
                if len(found) >= 6:
                    break
            if len(found) >= 3:
                break

    if not found and section_text:
        parts = re.split(r"(?<=[.!?])\s+", section_text)
        for p in parts:
            p = p.strip()
            if len(p) >= 30:
                found.append(p[:400])
            if len(found) >= 3:
                break

    if not found:
        return [_PLACEHOLDER_OBJ], 0.15

    conf = 0.7 if sec_conf >= 0.5 else 0.45
    if "objetivo geral" in (section_text or "").lower():
        conf = max(conf, 0.8)
    return found[:6], conf


def _guess_summary(blob: str) -> tuple[str, float]:
    section, conf = _section(blob, *_SECTION_ALIASES["summary"], max_chars=1400)
    if section and len(section) >= 80:
        return section, max(conf, 0.75)

    # Fallback: primeiro bloco útil após o título (evita sumário).
    lines = [ln.strip() for ln in blob.splitlines() if ln.strip()]
    paras: list[str] = []
    buf: list[str] = []
    for ln in lines[3:80]:
        low = ln.lower()
        if low.startswith("sumário") or low.startswith("sumario"):
            continue
        if re.match(r"^\d+\.\s+\S+", ln) and "·" in ln:
            continue
        if re.match(r"^\d+\.\s+(resumo|identifica|objetivo|metodolog)", low):
            if buf:
                break
            continue
        if len(ln) < 40 and not buf:
            continue
        buf.append(ln)
        if ln.endswith(".") or len(" ".join(buf)) > 200:
            paras.append(re.sub(r"\s+", " ", " ".join(buf)).strip())
            buf = []
        if sum(len(p) for p in paras) >= 500:
            break
    if buf:
        paras.append(re.sub(r"\s+", " ", " ".join(buf)).strip())
    summary = " ".join(paras).strip()[:1200]
    if len(summary) >= 80:
        return summary, 0.4
    # Último recurso: não devolver o PDF inteiro cru — só aviso.
    return (
        "Nao foi possivel isolar um resumo claro. Revise o PDF e edite este campo.",
        0.1,
    )


def _guess_areas(lower: str) -> list[str]:
    areas: list[str] = []
    for label, kws in _AREA_TAXONOMY:
        if any(kw in lower for kw in kws):
            if label not in areas:
                areas.append(label)
    return areas[:8]


def _guess_budget(blob: str) -> tuple[str | None, float]:
    patterns = (
        r"(?:valor\s+total|or[cç]amento\s+total|investimento\s+total).{0,40}?R\$\s*([\d\.\,]+)",
        r"R\$\s*([\d\.\,]{6,}).{0,40}?(?:valor\s+total|or[cç]amento)",
        r"(?:dura[cç][aã]o\s*/\s*valor|dura[cç][aã]o\s*/\s*valor).{0,20}?R\$\s*([\d\.\,]+)",
        r"/\s*R\$\s*([\d\.\,]{6,})",
    )
    for pat in patterns:
        m = re.search(pat, blob, flags=re.I | re.S)
        if m:
            return m.group(1), 0.75
    m = re.search(r"R\$\s*([\d\.\,]{6,})", blob)
    if m:
        return m.group(1), 0.45
    return None, 0.0


def _guess_duration(blob: str) -> tuple[int | None, float]:
    m = re.search(
        r"(?:dura[cç][aã]o|prazo|executado\s+em|cronograma).{0,40}?(\d{1,2})\s*(?:meses|m[eê]s)",
        blob,
        flags=re.I | re.S,
    )
    if m:
        return int(m.group(1)), 0.8
    m = re.search(r"(\d{1,2})\s*meses", blob, flags=re.I)
    if m:
        val = int(m.group(1))
        if 3 <= val <= 60:
            return val, 0.5
    return None, 0.0


def _guess_counterpart(blob: str) -> tuple[str, float]:
    section, conf = _section(blob, *_SECTION_ALIASES["counterpart"], max_chars=800)
    if section:
        return section, conf

    snippets: list[str] = []
    for m in re.finditer(
        r"(?is)contrapartida[^\n.]{0,40}R\$\s*[\d\.\,]+[^\n.]{0,80}",
        blob,
    ):
        sn = re.sub(r"\s+", " ", m.group(0)).strip()
        if sn and sn not in snippets:
            snippets.append(sn)
        if len(snippets) >= 3:
            break
    if snippets:
        return " ".join(snippets)[:900], 0.65
    return "", 0.0


def weak_fields(form: dict[str, Any], *, min_conf: float = 0.55) -> list[str]:
    """Campos que merecem reforço via LLM."""
    conf = form.get("confidence") or {}
    weak: list[str] = []
    for key in (
        "summary",
        "objectives",
        "methodology",
        "expected_results",
        "team",
        "counterpart",
        "areas",
        "budget_brl",
        "duration_months",
        "title",
    ):
        val = form.get(key)
        c = float(conf.get(key, 0.0) or 0.0)
        empty = val in (None, "", [], {})
        if key == "objectives" and isinstance(val, list):
            empty = (not val) or (val == [_PLACEHOLDER_OBJ]) or (val == [_PLACEHOLDER_OBJ_EMPTY])
        if key == "areas" and isinstance(val, list):
            empty = len(val) == 0
        if empty or c < min_conf:
            weak.append(key)
    return weak


def guess_form_fields(text: str, filename: str = "") -> dict[str, Any]:
    """Extrai campos editáveis básicos (heurística; o agente pode enriquecer com Ollama)."""
    blob = _normalize_ws(text or "")
    lower = blob.lower()
    useful = len(re.sub(r"\s+", "", blob)) >= 80

    confidence: dict[str, float] = {}
    evidence: dict[str, str] = {}

    if not useful:
        return {
            "title": filename or "Projeto",
            "summary": (
                "Nao foi possivel extrair texto util do PDF (pode ser escaneado). "
                "Preencha o formulario manualmente."
            ),
            "objectives": [_PLACEHOLDER_OBJ_EMPTY],
            "methodology": "",
            "expected_results": "",
            "team": "",
            "budget_brl": None,
            "duration_months": None,
            "areas": [],
            "counterpart": "",
            "notes": "PDF com pouco texto extraivel. Preencha manualmente ou use um PDF com texto selecionavel.",
            "extraction_ok": False,
            "extracted_chars": len(blob),
            "confidence": {k: 0.0 for k in (
                "title", "summary", "objectives", "methodology", "expected_results",
                "team", "budget_brl", "duration_months", "areas", "counterpart",
            )},
            "evidence": {},
            "extraction_method": "heuristic",
        }

    title = guess_title(blob, fallback=filename or "Projeto")
    confidence["title"] = 0.7 if "SEMENTE" in title.upper() or len(title) > 25 else 0.55
    evidence["title"] = title[:180]

    summary, conf_sum = _guess_summary(blob)
    confidence["summary"] = conf_sum
    evidence["summary"] = summary[:220]

    objectives, conf_obj = _objectives(blob)
    confidence["objectives"] = conf_obj
    evidence["objectives"] = (objectives[0] if objectives else "")[:220]

    methodology, conf_met = _section(blob, *_SECTION_ALIASES["methodology"])
    confidence["methodology"] = conf_met
    evidence["methodology"] = methodology[:220]

    expected, conf_exp = _section(blob, *_SECTION_ALIASES["expected_results"])
    confidence["expected_results"] = conf_exp
    evidence["expected_results"] = expected[:220]

    team, conf_team = _section(blob, *_SECTION_ALIASES["team"])
    confidence["team"] = conf_team
    evidence["team"] = team[:220]

    budget, conf_bud = _guess_budget(blob)
    confidence["budget_brl"] = conf_bud
    if budget:
        evidence["budget_brl"] = f"R$ {budget}"

    duration, conf_dur = _guess_duration(blob)
    confidence["duration_months"] = conf_dur
    if duration:
        evidence["duration_months"] = f"{duration} meses"

    areas = _guess_areas(lower)
    confidence["areas"] = 0.7 if areas else 0.2
    evidence["areas"] = "; ".join(areas)

    counterpart, conf_cp = _guess_counterpart(blob)
    confidence["counterpart"] = conf_cp
    evidence["counterpart"] = counterpart[:220]

    notes = (
        "Campos preenchidos automaticamente a partir do PDF — revise antes de avaliar."
    )

    # Rubricas nomeadas (quando o PDF lista Pessoal/Equipamentos/etc.)
    budget_items: dict[str, float] = {}
    try:
        from agents.project_risk import parse_budget_items_from_text

        budget_items = parse_budget_items_from_text(blob)
    except Exception:  # noqa: BLE001
        budget_items = {}

    out = {
        "title": title,
        "summary": summary,
        "objectives": objectives,
        "methodology": methodology,
        "expected_results": expected,
        "team": team,
        "budget_brl": budget,
        "duration_months": duration,
        "areas": areas,
        "counterpart": counterpart,
        "notes": notes,
        "extraction_ok": True,
        "extracted_chars": len(blob),
        "confidence": confidence,
        "evidence": evidence,
        "extraction_method": "heuristic",
    }
    if budget_items:
        out["budget_items"] = budget_items
    return out
