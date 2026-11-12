"""Corpus v2 — projetos GOOD (02–06) e BAD (01–06) em exemplos_projetos."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from agents.retrieval_agent import CompanyProfile, EdictMatch, ProjectQuery
from tests.fixtures.sads_exemplo_loader import _parse_money

EXEMPLOS_DIR = Path(__file__).resolve().parents[2] / "docs" / "TCC" / "exemplos_projetos"

CORPUS_V2_FILES: dict[str, str] = {
    "GOOD_02": "02_REDE_FRIA_CIRCULAR.pdf",
    "GOOD_03": "03_PONTE_LEITORA.pdf",
    "GOOD_04": "04_AQUA_SENTINELA.pdf",
    "GOOD_05": "05_ROTA_SEGURA.pdf",
    "GOOD_06": "06_BIOFILME_PAC.pdf",
    "BAD_01": "BAD_01_CLINICA_AI.pdf",
    "BAD_02": "BAD_02_SOLAR_BAIRRO.pdf",
    "BAD_03": "BAD_03_RECICLA_PLUS.pdf",
    "BAD_04": "BAD_04_SENSOR_CAMPO.pdf",
    "BAD_05": "BAD_05_CAPACITA_FUTURO.pdf",
    "BAD_06": "BAD_06_BATERIA_VERDE.pdf",
}

GABARITO_V2: dict[str, dict[str, Any]] = {
    "GOOD_02": {
        "alias": "Rede Fria Circular",
        "expect": "pass_rd",
        "must_have_tech_risk": True,
        "uf": "SC",
        "notes": "P&D refrigeração baixo carbono TRL4→7",
    },
    "GOOD_03": {
        "alias": "Ponte Leitora",
        "expect": "pass_rd",
        "must_have_tech_risk": True,
        "uf": "PE",
        "notes": "Edtech acessível TRL5→8",
    },
    "GOOD_04": {
        "alias": "Aqua Sentinela",
        "expect": "pass_rd",
        "must_have_tech_risk": True,
        "uf": "MG",
        "notes": "Sensores água TRL4→7",
    },
    "GOOD_05": {
        "alias": "Rota Segura",
        "expect": "pass_rd",
        "must_have_tech_risk": True,
        "uf": "GO",
        "notes": "Mobilidade escolar rural TRL5→8",
    },
    "GOOD_06": {
        "alias": "Biofilme PAC",
        "expect": "pass_rd",
        "must_have_tech_risk": True,
        "uf": "PR",
        "notes": "Biomaterial embalagem TRL3→7",
    },
    "BAD_01": {
        "alias": "Clínica AI",
        "expect": "fail_quality",
        "must_have_tech_risk": None,  # indiferente; qualidade ruim
        "notes": "Sem rubricas, metas, baseline — proposta oca",
    },
    "BAD_02": {
        "alias": "Solar Bairro",
        "expect": "block_no_tech_risk",
        "must_have_tech_risk": False,
        "notes": "Instalação de placas; sem adicionalidade P&D",
    },
    "BAD_03": {
        "alias": "Recicla Plus",
        "expect": "alert_marketing",
        "must_have_tech_risk": None,
        "notes": "Marketing R$ 4,8 mi — rubrica vedada",
    },
    "BAD_04": {
        "alias": "Sensor Campo",
        "expect": "alert_budget_math",
        "must_have_tech_risk": None,
        "notes": "1,8+1,4+0,9=4,1 ≠ 3,75",
    },
    "BAD_05": {
        "alias": "Capacita Futuro",
        "expect": "block_no_tech_risk",
        "must_have_tech_risk": False,
        "notes": "Cursos digitais sem P&D; orçamento não informado",
    },
    "BAD_06": {
        "alias": "Bateria Verde",
        "expect": "alert_budget_math",
        "must_have_tech_risk": True,  # há pesquisa, mas orçamento inconsistente
        "notes": "5+2+2,5=9,5 ≠ 9,0",
    },
}


@dataclass
class CorpusV2Example:
    key: str
    file_name: str
    raw_text: str
    title: str
    company_name: str
    uf: str | None
    trl: int | None
    budget_brl: float | None
    budget_items: dict[str, float]
    form_data: dict[str, Any]
    company: CompanyProfile
    project: ProjectQuery


def _extract(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _parse_trl(text: str) -> int | None:
    m = re.search(r"TRL\s*(\d+)\s*→\s*TRL\s*\d+", text, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    m2 = re.search(r"TRL\s*[=:]?\s*(\d{1,2})", text, flags=re.IGNORECASE)
    return int(m2.group(1)) if m2 else None


def _parse_uf(text: str) -> str | None:
    # Joinville–SC / Recife–PE / Belo Horizonte–MG
    m = re.search(r"[–\-]\s*([A-Z]{2})\b", text)
    if m:
        return m.group(1)
    m2 = re.search(r"Sede\s*\n\s*.*?([A-Z]{2})\b", text)
    return m2.group(1) if m2 else None


def _parse_proponent(text: str) -> str:
    m = re.search(r"Proponente\s*\n\s*(.+)", text)
    return m.group(1).strip() if m else "Proponente"


def _parse_title(text: str, fallback: str) -> str:
    first = text.strip().split("\n")[0].strip()
    if first and "PROPOSTA" not in first.upper() and len(first) > 5:
        # título pode ocupar 2–3 linhas
        lines = [ln.strip() for ln in text.strip().split("\n")[:4] if ln.strip()]
        title_parts = []
        for ln in lines:
            if ln.upper().startswith("PROPOSTA") or ln.upper().startswith("AREA"):
                break
            title_parts.append(ln)
        return " ".join(title_parts)[:180] or fallback
    m = re.search(r"^(.+?)\nPROPOSTA", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:180]
    return fallback


def _parse_budget_total(text: str) -> float | None:
    for pat in (
        r"Valor total\s*\n\s*R\$\s*([\d.]+)",
        r"Valor solicitado\s*\n\s*R\$\s*([\d.]+)",
        r"Valor total solicitado:\s*R\$\s*([\d.,]+)",
        r"total declarado R\$\s*([\d.,]+)",
        r"total informado R\$\s*([\d.,]+)",
        r"Total R\$\s*([\d.,]+)",
    ):
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            raw = m.group(1)
            # 8.200.000 (BR) ou 4.200.000
            if re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):
                return float(raw.replace(".", ""))
            # 6,5 milhoes handled below
            val = _parse_money(raw)
            if val is not None:
                return val
    # "R$ 6.500.000" / "R$ 6,5 milhoes"
    m = re.search(r"R\$\s*([\d.]+)\s*milh", text, flags=re.IGNORECASE)
    if m:
        n = _parse_money(m.group(1).replace(".", "")) if "." in m.group(1) else _parse_money(m.group(1))
        if n and n < 1000:
            return n * 1_000_000
        if n:
            return n
    m2 = re.search(r"R\$\s*([\d]+(?:[.,]\d+)?)\s*milh", text, flags=re.IGNORECASE)
    if m2:
        n = _parse_money(m2.group(1))
        if n is not None:
            return n * 1_000_000 if n < 1000 else n
    return None


def _parse_budget_items_v2(text: str) -> dict[str, float]:
    items: dict[str, float] = {}
    # Tabela GOOD: Nome\n2.350.000
    for name, val in re.findall(
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 ,;&/\-]{3,60})\s*\n\s*([\d]{1,3}(?:\.\d{3})+)",
        text,
    ):
        key = name.strip()
        if key.lower() in {"categoria", "valor", "justificativa", "fase", "período", "periodo"}:
            continue
        items[key] = float(val.replace(".", ""))

    # BAD estilo: "Software R$ 700 mil; marketing R$ 4,8 milhoes"
    for name, num, unit in re.findall(
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ ]{2,30})\s*R\$\s*([\d.,]+)\s*(milh(?:[oõ]es)?|mil)?",
        text,
        flags=re.IGNORECASE,
    ):
        key = name.strip(" :;-")
        n = _parse_money(num)
        if n is None:
            continue
        unit_l = (unit or "").lower()
        if "milh" in unit_l:
            n *= 1_000_000
        elif unit_l == "mil":
            n *= 1_000
        if key.lower() not in {"valor", "total"}:
            items[key] = n

    # "Pessoal R$ 1,8 milhao; equipamentos R$ 1,4 milhao; viagens R$ 900 mil"
    for name, num, unit in re.findall(
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ ]{2,24})\s*R\$\s*([\d.,]+)\s*(milh[aã]o|milh[oõ]es|mil)",
        text,
        flags=re.IGNORECASE,
    ):
        key = name.strip()
        n = _parse_money(num)
        if n is None:
            continue
        if "milh" in unit.lower():
            n *= 1_000_000
        else:
            n *= 1_000
        items[key] = n

    return items


def _areas_from_text(text: str) -> list[str]:
    low = text.lower()
    mapping = [
        ("refriger", "energia"),
        ("alfabetiza", "educacao"),
        ("água", "saneamento"),
        ("agua", "saneamento"),
        ("escolar", "mobilidade"),
        ("embalagem", "materiais"),
        ("biodegrad", "materiais"),
        ("saúde", "saude"),
        ("saude", "saude"),
        ("solar", "energia"),
        ("recicl", "economia_circular"),
        ("lavoura", "agro"),
        ("agroneg", "agro"),
        ("bateria", "energia"),
        ("curso", "educacao"),
    ]
    out: list[str] = []
    for needle, area in mapping:
        if needle in low and area not in out:
            out.append(area)
    return out or ["inovacao"]


def parse_corpus_v2(key: str) -> CorpusV2Example:
    fname = CORPUS_V2_FILES[key]
    path = EXEMPLOS_DIR / fname
    if not path.exists():
        raise FileNotFoundError(path)
    text = _extract(path)
    title = _parse_title(text, fname)
    company_name = _parse_proponent(text)
    uf = _parse_uf(text) or GABARITO_V2[key].get("uf")
    trl = _parse_trl(text)
    budget = _parse_budget_total(text)
    items = _parse_budget_items_v2(text)
    areas = _areas_from_text(text)

    # Porte default EPP para GOOD; BAD sem porte explícito
    size = "EPP"
    if "instituto" in company_name.lower():
        size = "EPP"
    if "s.a." in company_name.lower() or "s.a" in company_name.lower():
        size = "Media"

    form_data: dict[str, Any] = {
        "title": title,
        "summary": text[:2000],
        "trl": trl,
        "budget_brl": budget,
        "budget_items": items,
        "areas": areas,
        "notes": text[2000:5000],
        "corpus_key": key,
    }
    company = CompanyProfile(
        name=company_name,
        size=size,
        trl=trl,
        areas=areas,
        uf=uf,
        revenue_brl=3_000_000.0 if key.startswith("GOOD") else 800_000.0,
    )
    project = ProjectQuery(
        title=title,
        text=text[:7000],
        budget_brl=budget,
        form_data=form_data,
    )
    return CorpusV2Example(
        key=key,
        file_name=fname,
        raw_text=text,
        title=title,
        company_name=company_name,
        uf=uf,
        trl=trl,
        budget_brl=budget,
        budget_items=items,
        form_data=form_data,
        company=company,
        project=project,
    )


def load_corpus_v2() -> dict[str, CorpusV2Example]:
    return {k: parse_corpus_v2(k) for k in CORPUS_V2_FILES}


def synthetic_matches_for(key: str) -> list[EdictMatch]:
    common = dict(year=2026, url=None, distance=0.15, reasons=[], excerpt="")
    ideal_title = {
        "GOOD_02": "FINEP Mais Inovação — Eficiência Energética Industrial",
        "GOOD_03": "FINEP / CNPq — Tecnologias Assistivas e Educação",
        "GOOD_04": "FINEP Saneamento / Recursos Hídricos",
        "GOOD_05": "FINEP Mobilidade e Cidades Inteligentes",
        "GOOD_06": "FINEP Bioeconomia / Materiais Avançados",
    }.get(key, "FINEP Subvenção Inovação")
    areas = {
        "GOOD_02": ["energia", "inovacao"],
        "GOOD_03": ["educacao", "inovacao"],
        "GOOD_04": ["saneamento", "inovacao"],
        "GOOD_05": ["mobilidade", "inovacao"],
        "GOOD_06": ["materiais", "inovacao"],
    }.get(key, ["inovacao"])

    matches = [
        EdictMatch(
            external_id=f"ideal-{key}",
            title=ideal_title,
            agency="FINEP",
            areas=areas,
            similarity=0.9,
            region="Todo Brasil",
            instrument="subvencao",
            company_sizes=["ME", "EPP", "Media"],
            min_trl=3,
            **common,
        ),
        EdictMatch(
            external_id="trap-semi",
            title="FINEP Subvenção Econômica Semicondutores",
            agency="FINEP",
            areas=["semicondutores"],
            similarity=0.82,
            region="Todo Brasil",
            instrument="subvencao",
            **common,
        ),
        EdictMatch(
            external_id="trap-centelha",
            title="Centelha 3 — exclusivo MPE",
            agency="CENTELHA",
            areas=["inovacao"],
            similarity=0.7,
            region="Todo Brasil",
            instrument="subvencao",
            company_sizes=["MEI", "ME", "EPP"],
            **common,
        ),
    ]
    return matches
