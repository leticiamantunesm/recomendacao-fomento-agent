"""Heurísticas para pré-preencher formulário de projeto a partir do PDF."""

from __future__ import annotations

import re
from typing import Any


def guess_title(text: str, fallback: str = "Projeto sem titulo") -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    skip = ("página", "pagina", "confidential", "sumário", "sumario", "índice", "indice")
    for ln in lines[:40]:
        low = ln.lower()
        if any(s in low for s in skip):
            continue
        if 12 <= len(ln) <= 180 and not low.startswith("http"):
            return ln[:300]
    if lines:
        return lines[0][:300]
    return fallback[:300]


def _section(blob: str, *headers: str, max_chars: int = 900) -> str:
    """Pega o bloco apos um cabecalho ate o proximo cabecalho tipico."""
    for h in headers:
        pat = rf"(?is)(?:^|\n)\s*{h}\s*[:\-]?\s*\n(.+?)(?=\n\s*(?:\d+[\.\)]\s*)?(?:objetivo|metodolog|resultado|equipe|cronograma|orcamento|orçamento|justificativa|referenc|anexo)\b|\Z)"
        m = re.search(pat, blob)
        if m:
            chunk = re.sub(r"\s+", " ", m.group(1)).strip()
            if len(chunk) > 40:
                return chunk[:max_chars]
    return ""


def _objectives(blob: str) -> list[str]:
    found: list[str] = []
    for pat in (
        r"(?is)objetivos?\s+geral(?:es)?\s*[:\-–]\s*(.+?)(?=\n\s*objetivo|\n\s*\d+\.|\Z)",
        r"(?is)objetivo[s]?\s*[:\-–]\s*(.+?)(?=\n\s*(?:metodolog|resultado|justific)|\Z)",
    ):
        m = re.search(pat, blob)
        if m:
            line = re.sub(r"\s+", " ", m.group(1)).strip()[:500]
            if line:
                found.append(line)
                break
    # bullets
    for m in re.finditer(r"(?m)^\s*[\-\*•]\s*(.+)$", blob):
        t = m.group(1).strip()
        if 20 <= len(t) <= 240 and "objetivo" not in t.lower():
            found.append(t)
        if len(found) >= 5:
            break
    if not found:
        found = ["Descrever objetivos alinhados ao edital (editar)."]
    return found[:5]


def guess_form_fields(text: str, filename: str = "") -> dict[str, Any]:
    """Extrai campos editaveis basicos (Fase A — heuristico, nao LLM)."""
    blob = text or ""
    lower = blob.lower()
    useful = len(re.sub(r"\s+", "", blob)) >= 80

    budget = None
    m_budget = re.search(
        r"(?:or[cç]amento|valor\s+total|investimento|recursos?).{0,40}?R\$\s*([\d\.\,]+)",
        blob,
        flags=re.I | re.S,
    )
    if m_budget:
        budget = m_budget.group(1)

    duration = None
    m_dur = re.search(
        r"(?:dura[cç][aã]o|prazo|cronograma).{0,40}?(\d{1,2})\s*(?:meses|m[eê]s)",
        blob,
        flags=re.I | re.S,
    )
    if m_dur:
        duration = int(m_dur.group(1))

    areas: list[str] = []
    for kw in (
        "inovacao",
        "inovação",
        "inteligencia artificial",
        "inteligência artificial",
        "startup",
        "biotecnologia",
        "saude",
        "saúde",
        "energia",
        "agro",
        "industria 4.0",
        "indústria 4.0",
        "sustentab",
        "digital",
    ):
        if kw in lower and kw not in areas:
            areas.append(kw)

    summary = " ".join(blob.split())[:1200] if useful else (
        "Nao foi possivel extrair texto util do PDF (pode ser escaneado). "
        "Preencha o formulario manualmente."
    )

    notes = (
        "Campos preenchidos automaticamente a partir do PDF — revise antes de avaliar."
        if useful
        else "PDF com pouco texto extraivel. Preencha manualmente ou use um PDF com texto selecionavel."
    )

    return {
        "title": guess_title(blob, fallback=filename or "Projeto") if useful else (filename or "Projeto"),
        "summary": summary,
        "objectives": _objectives(blob) if useful else ["Descrever objetivos do projeto."],
        "methodology": _section(blob, "metodologia", "método", "metodo", "abordagem"),
        "expected_results": _section(blob, "resultados esperados", "resultados", "entregas", "produtos"),
        "team": _section(blob, "equipe", "equipe técnica", "equipe tecnica", "recursos humanos"),
        "budget_brl": budget,
        "duration_months": duration,
        "areas": areas[:8],
        "counterpart": _section(blob, "contrapartida", "contrapartidas"),
        "notes": notes,
        "extraction_ok": useful,
        "extracted_chars": len(blob),
    }
