"""Carrega PDFs estruturados de exemplos_projetos → perfis para scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from agents.retrieval_agent import CompanyProfile, EdictMatch, ProjectQuery
from tests.fixtures.sads_exemplos_gabarito import EXEMPLOS_DIR, PROJECT_FILES


@dataclass
class ParsedExample:
    project_id: str
    file_name: str
    raw_text: str
    title: str
    company_name: str
    size: str | None
    revenue_brl: float | None
    uf: str | None
    city: str | None
    trl: int | None
    budget_brl: float | None
    budget_items: dict[str, float]
    form_data: dict[str, Any]
    company: CompanyProfile
    project: ProjectQuery


def _parse_money(raw: str | None) -> float | None:
    """Aceita US (1,200,000.00) e BR (1.200.000,00)."""
    if not raw:
        return None
    s = str(raw).strip()
    s = re.sub(r"[^\d,.\-]", "", s)
    if not s:
        return None
    # US: 1,200,000.00 ou 700,000.00
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    # BR: 1.200.000,00
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", s):
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." in s:
        # fallback: último separador é decimal
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        # 1200,50 (BR decimal) vs 1,200 (US thousands sem centavos)
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _field(text: str, label: str) -> str | None:
    # Label em uma linha, valor na seguinte (padrão dos PDFs de teste)
    pat = rf"{re.escape(label)}\s*\n\s*(.+)"
    m = re.search(pat, text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Mesma linha
    m2 = re.search(rf"{re.escape(label)}\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE)
    if m2:
        return m2.group(1).strip().split("\n")[0].strip()
    return None


def _infer_size(porte_line: str | None) -> tuple[str | None, float | None]:
    if not porte_line:
        return None, None
    low = porte_line.lower()
    revenue = None
    money = re.search(r"R\$\s*([\d.,]+)", porte_line)
    if money:
        revenue = _parse_money(money.group(1))
    if "pessoa física" in low or "pessoa fisica" in low:
        return "PF", revenue
    if "grande" in low:
        return "Grande", revenue
    if "média" in low or "media" in low:
        return "Media", revenue
    if "epp" in low or "pequeno porte" in low:
        return "EPP", revenue
    if "microempresa" in low or re.search(r"\bme\b", low):
        return "ME", revenue
    if "mei" in low:
        return "MEI", revenue
    return None, revenue


def _infer_uf(sede: str | None) -> tuple[str | None, str | None]:
    if not sede:
        return None, None
    # "Piracicaba / SP" ou "Londrina / PR"
    m = re.search(r"/\s*([A-Z]{2})\b", sede)
    uf = m.group(1) if m else None
    city = sede.split("/")[0].strip() if "/" in sede else sede.strip()
    return uf, city


def _parse_budget_items(text: str) -> dict[str, float]:
    items: dict[str, float] = {}
    # Após cabeçalho de rubricas, linhas "Nome\nR$ valor"
    section = re.search(
        r"Detalhamento de Rubricas(.*?)(?:5\.\s*Gabarito|Enquadramento Ideal|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    blob = section.group(1) if section else text
    pairs = re.findall(
        r"([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9 \-]{2,60})\s*\n\s*R\$\s*([\d.,]+)",
        blob,
    )
    skip = {"rubrica", "categoria", "valor", "despesa", "alocado"}
    for name, val in pairs:
        key = name.strip()
        if key.lower() in skip or "valor alocado" in key.lower():
            continue
        n = _parse_money(val)
        if n is not None:
            items[key] = n
    return items


def parse_example_pdf(project_id: str, path: Path | None = None) -> ParsedExample:
    fname = PROJECT_FILES[project_id]
    pdf_path = path or (EXEMPLOS_DIR / fname)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    text = extract_pdf_text(pdf_path)

    title_m = re.search(r"PROPOSTA DE PROJETO:\s*(.+)", text)
    title = (title_m.group(1).strip() if title_m else pdf_path.stem)[:200]

    company_name = _field(text, "Razão Social:") or _field(text, "Razão Social") or "Empresa"
    porte_line = _field(text, "Porte / Faturamento Anual:") or _field(
        text, "Porte / Faturamento Anual"
    )
    size, revenue = _infer_size(porte_line)
    sede = _field(text, "Sede / Localização:") or _field(text, "Sede / Localização")
    uf, city = _infer_uf(sede)

    trl_raw = _field(text, "Maturidade Atual (TRL)")
    trl = int(trl_raw) if trl_raw and trl_raw.strip().isdigit() else None

    budget_raw = _field(text, "Orçamento Total Solicitado")
    budget = _parse_money(budget_raw)
    items = _parse_budget_items(text)

    # Áreas heurísticas a partir do título/resumo
    areas: list[str] = []
    low = text.lower()
    area_map = [
        ("soja", "agro"),
        ("agrícola", "agro"),
        ("agricultura", "agro"),
        ("canav", "agro"),
        ("drone", "agro"),
        ("médic", "saude"),
        ("saúde", "saude"),
        ("arritm", "saude"),
        ("peptídeo", "biotecnologia"),
        ("alzheimer", "biotecnologia"),
        ("polímero", "materiais"),
        ("embalag", "materiais"),
        ("documentário", "audiovisual"),
        ("audiovisual", "audiovisual"),
        ("criptograf", "ti"),
        ("hidrogênio", "energia"),
        ("eletrolis", "energia"),
        ("logíst", "logistica"),
        ("roteiriza", "logistica"),
        ("padaria", "comercio"),
        ("forno", "comercio"),
        ("inovacao", "inovacao"),
    ]
    for needle, area in area_map:
        if needle in low and area not in areas:
            areas.append(area)

    form_data: dict[str, Any] = {
        "title": title,
        "summary": text[:1500],
        "trl": trl,
        "budget_brl": budget,
        "budget_items": items,
        "areas": areas,
        "notes": text[1500:4000],
        "project_id_teste": project_id,
    }

    company = CompanyProfile(
        name=company_name,
        size=size,
        trl=trl,
        areas=areas,
        uf=uf,
        revenue_brl=revenue,
    )
    # Pessoa física: marcar size PF se CPF
    if re.search(r"pessoa f[ií]sica|via cpf", text, flags=re.IGNORECASE):
        company.size = "PF"

    project = ProjectQuery(
        title=title,
        text=text[:6000],
        budget_brl=budget,
        form_data=form_data,
    )
    return ParsedExample(
        project_id=project_id,
        file_name=fname,
        raw_text=text,
        title=title,
        company_name=company_name,
        size=company.size,
        revenue_brl=revenue,
        uf=uf,
        city=city,
        trl=trl,
        budget_brl=budget,
        budget_items=items,
        form_data=form_data,
        company=company,
        project=project,
    )


def load_all_examples() -> dict[str, ParsedExample]:
    out: dict[str, ParsedExample] = {}
    for pid in PROJECT_FILES:
        out[pid] = parse_example_pdf(pid)
    return out


def trap_and_ideal_edicts(project_id: str) -> list[EdictMatch]:
    """Editais sintéticos: ideal + armadilhas para validar hard gates."""
    common = dict(year=2026, url=None, distance=0.2, reasons=[], excerpt="")
    traps = [
        EdictMatch(
            external_id="trap-semi",
            title="FINEP Subvenção Econômica Semicondutores",
            agency="FINEP",
            areas=["semicondutores"],
            similarity=0.88,
            region="Todo Brasil",
            instrument="subvencao",
            **common,
        ),
        EdictMatch(
            external_id="trap-h2",
            title="FINEP Transição Energética Hidrogênio Verde",
            agency="FINEP",
            areas=["energia", "hidrogênio"],
            similarity=0.75,
            region="Todo Brasil",
            instrument="subvencao",
            **common,
        ),
        EdictMatch(
            external_id="trap-centelha",
            title="Centelha 3 — exclusivo MPE/startup",
            agency="CENTELHA",
            areas=["inovacao"],
            similarity=0.7,
            region="Todo Brasil",
            instrument="subvencao",
            company_sizes=["MEI", "ME", "EPP"],
            **common,
        ),
        EdictMatch(
            external_id="trap-fapesp-sp",
            title="FAPESP PIPE Fase 2 — Estado de São Paulo",
            agency="FAPESP",
            areas=["inovacao"],
            similarity=0.8,
            region="São Paulo",
            instrument="subvencao",
            company_sizes=["ME", "EPP"],
            **common,
        ),
        EdictMatch(
            external_id="trap-credito-pj",
            title="BNDES — Financiamento PJ (crédito institucional)",
            agency="BNDES",
            areas=["investimento"],
            similarity=0.65,
            region="Todo Brasil",
            instrument="credito",
            **common,
        ),
    ]

    ideals: dict[str, EdictMatch] = {
        "01": EdictMatch(
            external_id="ideal-01",
            title="FAPESP PIPE Fase 2 / Centelha SP",
            agency="FAPESP",
            areas=["agro", "inovacao"],
            similarity=0.92,
            region="São Paulo",
            instrument="subvencao",
            company_sizes=["ME", "EPP"],
            min_trl=3,
            **common,
        ),
        "02": EdictMatch(
            external_id="ideal-02",
            title="Tecnova III RS / FINEP Mais Inovação Saúde",
            agency="FINEP",
            areas=["saude", "inovacao"],
            similarity=0.91,
            region="Sul",
            instrument="subvencao",
            company_sizes=["ME", "EPP"],
            min_trl=6,
            **common,
        ),
        "07": EdictMatch(
            external_id="ideal-07",
            title="ProAC Editais / Lei Rouanet — Audiovisual",
            agency="CULTSP",
            areas=["audiovisual", "cultura"],
            similarity=0.95,
            region="São Paulo",
            instrument="outro",
            **common,
        ),
        "09": EdictMatch(
            external_id="ideal-09",
            title="EMBRAPII / FINEP Transição Energética Hidrogênio Verde",
            agency="EMBRAPII",
            areas=["energia", "hidrogênio"],
            similarity=0.93,
            region="Todo Brasil",
            instrument="parceria",
            min_trl=4,
            **common,
        ),
    }

    matches = list(traps)
    if project_id in ideals:
        matches.insert(0, ideals[project_id])
    return matches
