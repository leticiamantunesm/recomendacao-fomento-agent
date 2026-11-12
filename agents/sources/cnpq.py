"""Fonte CNPq — chamadas abertas para submissao (gov.br/Plone).

Portal: https://www.gov.br/cnpq/pt-br/chamadas/abertas-para-submissao
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from agents.sources.base import (
    OpenCall,
    absolute_url,
    br_date_to_iso,
    clean_text,
    fetch_html,
    parse_br_date,
    slug_id,
)

CNPQ_OPEN_URL = "https://www.gov.br/cnpq/pt-br/chamadas/abertas-para-submissao"
CNPQ_BASE = "https://www.gov.br"


class CnpqSource:
    def close(self) -> None:
        return None

    def __enter__(self) -> CnpqSource:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def collect_calls(self, *, limit: int | None = None, only_open: bool = True) -> list[OpenCall]:
        html = fetch_html(CNPQ_OPEN_URL)
        soup = BeautifulSoup(html, "html.parser")
        content = soup.select_one("#content") or soup.select_one("main") or soup.body
        if content is None:
            return []

        now = datetime.now(timezone.utc)
        calls: list[OpenCall] = []
        for h2 in content.find_all("h2"):
            title = clean_text(h2.get_text(" ", strip=True))
            if len(title) < 12:
                continue
            if not re.search(r"chamada|cnpq", title, flags=re.I):
                continue

            summary_parts: list[str] = []
            insc_raw = ""
            detail_url = CNPQ_OPEN_URL
            themes: list[str] = []

            # Percorre ate o proximo h2 (conteudo pode estar em divs aninhados).
            for el in h2.find_all_next():
                name = getattr(el, "name", None)
                if name in {"h2", "h1"}:
                    break
                if name == "p":
                    text = clean_text(el.get_text(" ", strip=True))
                    if text and not text.lower().startswith("compartilhe") and len(summary_parts) < 3:
                        summary_parts.append(text)
                        if re.search(r"inscri", text, flags=re.I) and not insc_raw:
                            insc_raw = text
                if name == "li":
                    li_txt = clean_text(el.get_text(" ", strip=True))
                    if re.search(r"inscri", li_txt, flags=re.I):
                        insc_raw = li_txt
                    a = el.find("a", href=True)
                    if a and re.search(r"chamada|edital|pdf", a.get_text(" ", strip=True), flags=re.I):
                        href = a["href"]
                        if href.lower().endswith(".pdf") or "@@download" in href.lower() or "/chamadas/" in href.lower():
                            detail_url = absolute_url(CNPQ_BASE, href)

            # Datas: Inscrições: dd/mm/aaaa a dd/mm/aaaa
            vigencia_inicio = None
            prazo = None
            m = re.search(
                r"(\d{1,2}/\d{1,2}/\d{4}).{0,20}?(\d{1,2}/\d{1,2}/\d{4})",
                insc_raw,
            )
            if m:
                vigencia_inicio = br_date_to_iso(m.group(1))
                prazo = br_date_to_iso(m.group(2))
            elif insc_raw:
                prazo = br_date_to_iso(insc_raw)

            if only_open and prazo:
                from agents.sources.finep import parse_finep_datetime

                end = parse_finep_datetime(prazo) or parse_br_date(insc_raw)
                if end and end < now:
                    continue

            if "petrobras" in title.lower() or "energia" in " ".join(summary_parts).lower():
                themes.append("energia")
            if "biodivers" in title.lower():
                themes.append("biodiversidade")
            if "inova" in title.lower():
                themes.append("inovação")
            if "evento" in title.lower():
                themes.append("eventos científicos")
            if not themes:
                themes = ["ciência", "tecnologia", "inovação"]

            description = " ".join(summary_parts)
            if insc_raw:
                description = f"{description} {insc_raw}".strip()

            call = OpenCall(
                source="CNPQ",
                external_id=slug_id("cnpq", title),
                title=title[:300],
                detail_url=detail_url,
                situacao="Aberta",
                themes=themes,
                opportunity_type="Chamada pública CNPq",
                region="Brasil",
                vigencia_inicio=vigencia_inicio,
                prazo_proposta=prazo,
                description_text=description[:5000],
                raw={"inscricoes": insc_raw},
            )
            calls.append(call)
            if limit is not None and len(calls) >= limit:
                break
        return calls
