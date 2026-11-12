"""Fonte FAPESP — chamadas abertas com detalhe HTML + anexos.

Portal: https://fapesp.br/chamadas/
Detalhe: https://fapesp.br/{id}/… (meta-refresh a partir de /{id})
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from agents.sources.base import (
    OpenCall,
    absolute_url,
    br_date_to_iso,
    clean_text,
    download_binary,
    fetch_html,
    parse_br_date,
    slug_id,
)
from agents.sources.finep import parse_finep_datetime

FAPESP_URL = "https://fapesp.br/chamadas/"
FAPESP_BASE = "https://fapesp.br"

_SKIP_FILE_PATTERNS = (
    "csc.pdf",
    "manualcartaobb",
    "/publicacoes/",
    "carta-de-servicos",
    "carta de serviços",
)

_MENU_TITLES = {
    "Submissão de Propostas",
    "Execução de Processos",
    "Colaborações em Pesquisa",
    "Outros Links",
    "Impacto da Pesquisa na Sociedade",
    "Boas Práticas e Políticas",
    "Conselho Superior",
    "Transparência",
    "Colaborações",
    "Dados e Informações",
}


class FapespSource:
    def close(self) -> None:
        return None

    def __enter__(self) -> FapespSource:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def collect_calls(
        self,
        *,
        limit: int | None = None,
        only_open: bool = True,
        enrich_details: bool = True,
    ) -> list[OpenCall]:
        html = fetch_html(FAPESP_URL)
        soup = BeautifulSoup(html, "html.parser")
        now = datetime.now(timezone.utc)
        calls: list[OpenCall] = []
        seen: set[str] = set()

        for h in soup.find_all(["h3", "h4"]):
            title = clean_text(h.get_text(" ", strip=True))
            if len(title) < 15 or title in _MENU_TITLES:
                continue

            meta: dict[str, str] = {}
            link = FAPESP_URL
            a = h.find("a", href=True)
            if a:
                link = absolute_url(FAPESP_BASE, a["href"])
                title = clean_text(a.get_text(" ", strip=True)) or title

            for sib in h.next_siblings:
                name = getattr(sib, "name", None)
                if name in {"h2", "h3", "h4"}:
                    break
                text = clean_text(sib.get_text(" ", strip=True)) if getattr(sib, "get_text", None) else ""
                if not text:
                    continue
                low = text.lower()
                if "data-limite" in low or low.startswith("prazo"):
                    meta["prazo_raw"] = text
                    m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
                    if m:
                        meta["prazo"] = m.group(1)
                    elif "ano todo" in low or "fluxo contínuo" in low or "fluxo continuo" in low:
                        meta["prazo"] = ""
                        meta["continuo"] = "1"
                elif low.startswith("área") or low.startswith("area"):
                    meta["area"] = text.split(":", 1)[-1].strip()
                elif low.startswith("modalidade") or low.startswith("programa"):
                    meta["modalidade"] = text.split(":", 1)[-1].strip()
                elif name == "a" and sib.get("href"):
                    link = absolute_url(FAPESP_BASE, sib["href"])

            if "prazo_raw" not in meta and "continuo" not in meta:
                continue

            prazo_iso = br_date_to_iso(meta.get("prazo")) if meta.get("prazo") else None
            if only_open and prazo_iso:
                end = parse_finep_datetime(prazo_iso) or parse_br_date(meta.get("prazo"))
                if end and end < now:
                    continue

            ext = fapesp_external_id(link, title)
            if ext in seen:
                continue
            seen.add(ext)

            themes = _themes_from_meta(title, meta)
            desc_bits = [title]
            for key in ("prazo_raw", "area", "modalidade"):
                if meta.get(key):
                    desc_bits.append(meta[key])

            call = OpenCall(
                source="FAPESP",
                external_id=ext,
                title=title[:300],
                detail_url=link,
                situacao="Aberta",
                themes=themes,
                opportunity_type=meta.get("modalidade") or "Chamada FAPESP",
                region="SP / Brasil",
                prazo_proposta=prazo_iso,
                description_text=" | ".join(desc_bits)[:5000],
                raw=dict(meta),
            )
            if enrich_details and _looks_like_detail_url(link):
                try:
                    self.enrich_call(call)
                except Exception as exc:  # noqa: BLE001 — detalhe opcional
                    call.raw["enrich_error"] = str(exc)[:300]

            calls.append(call)
            if limit is not None and len(calls) >= limit:
                break
        return calls

    def enrich_call(self, call: OpenCall) -> OpenCall:
        """Resolve meta-refresh, extrai texto da chamada e lista anexos (pdf/doc)."""
        final_url = resolve_fapesp_detail_url(call.detail_url)
        call.detail_url = final_url
        html = fetch_html(final_url)
        soup = BeautifulSoup(html, "html.parser")
        content = soup.select_one(".content") or soup.find("main") or soup.body
        if content is None:
            return call

        text = _clean_detail_text(content.get_text("\n", strip=True))
        if len(text) > 400:
            call.description_text = text[:50000]

        published = re.search(
            r"Publicad[ao]\s+em\s+(\d{1,2}/\d{1,2}/\d{4})",
            text,
            flags=re.I,
        )
        if published:
            call.published_at = br_date_to_iso(published.group(1))

        prazo = re.search(
            r"(?:Data[- ]limite[^\n]{0,80}?|submiss[^\n]{0,40}?)(\d{1,2}/\d{1,2}/\d{4})",
            text,
            flags=re.I,
        )
        if prazo and not call.prazo_proposta:
            call.prazo_proposta = br_date_to_iso(prazo.group(1))

        modalidade = re.search(
            r"Modalidade(?:\s+de\s+Apoio)?\s*:\s*([^\n]+)",
            text,
            flags=re.I,
        )
        if modalidade and (
            not call.opportunity_type or call.opportunity_type == "Chamada FAPESP"
        ):
            call.opportunity_type = clean_text(modalidade.group(1))[:200]

        call.attachments = _extract_attachments(content, call.external_id, final_url)
        call.raw = {
            **(call.raw or {}),
            "detail_url_final": final_url,
            "detail_chars": len(text),
            "attachment_count": len(call.attachments),
        }
        return call

    def download_attachment(
        self,
        att: dict,
        dest_dir: Path,
    ) -> tuple[Path, bool]:
        url = str(att.get("pdf_url") or att.get("url") or "")
        name = str(att.get("pdf_name") or "")
        if not url or not name:
            raise ValueError("anexo FAPESP sem pdf_url/pdf_name")
        path = Path(dest_dir) / name
        return download_binary(url, path)


def fapesp_external_id(url: str, title: str) -> str:
    m = re.search(r"fapesp\.br/(\d{4,})", url or "", flags=re.I)
    if m:
        return f"fapesp-{m.group(1)}"
    return slug_id("fapesp", title)


def resolve_fapesp_detail_url(url: str) -> str:
    """Segue meta-refresh HTML (httpx nao segue http-equiv=refresh)."""
    html = fetch_html(url)
    if "http-equiv" in html.lower() and "refresh" in html.lower():
        m = re.search(
            r"content=['\"][^'\"]*URL=['\"]?([^'\">\s]+)['\"]?",
            html,
            flags=re.I,
        )
        if not m:
            m = re.search(r"URL=['\"]?([^'\">\s]+)", html, flags=re.I)
        if m:
            return absolute_url(FAPESP_BASE, m.group(1).strip("'\""))
    return url


def _looks_like_detail_url(url: str) -> bool:
    return bool(re.search(r"fapesp\.br/\d{4,}", url or "", flags=re.I))


def _themes_from_meta(title: str, meta: dict[str, str]) -> list[str]:
    themes: list[str] = []
    area = meta.get("area") or ""
    if area and "consulte" not in area.lower() and "todas" not in area.lower():
        themes.append(area)
    if "pipe" in title.lower() or "pipe" in (meta.get("modalidade") or "").lower():
        themes.extend(["inovação", "pequenas empresas", "PIPE"])
    if "amaz" in title.lower():
        themes.append("Amazônia")
    if not themes:
        themes = ["pesquisa", "FAPESP"]
    return list(dict.fromkeys(themes))


def _clean_detail_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text or "")
    # Remove blocos tipicos de acessibilidade/rodape curtos repetidos.
    lines = []
    for line in text.splitlines():
        low = line.strip().lower()
        if low in {"ferramentas de acessibilidade", "barra de ferramentas aberta"}:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _extract_attachments(content, external_id: str, page_url: str) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    idx = 0
    for a in content.find_all("a", href=True):
        href = absolute_url(page_url, a["href"])
        label = clean_text(a.get_text(" ", strip=True)) or unquote(Path(urlparse(href).path).name)
        if _is_noise_file(href, label):
            continue
        if not _is_document_href(href, label):
            continue
        key = href.split("?")[0].lower()
        if key in seen:
            continue
        seen.add(key)
        idx += 1
        pdf_name = _attachment_filename(external_id, href, label, idx)
        role = "edital" if idx == 1 and href.lower().endswith(".pdf") else "anexo"
        found.append(
            {
                "role": role,
                "pdf_url": href,
                "pdf_name": pdf_name,
                "original_name": label[:200] or pdf_name,
                "legenda": label[:200],
            }
        )
    return found


def _is_noise_file(href: str, label: str) -> bool:
    blob = f"{href} {label}".lower()
    return any(p in blob for p in _SKIP_FILE_PATTERNS)


def _is_document_href(href: str, label: str) -> bool:
    path = urlparse(href).path.lower()
    if path.endswith((".pdf", ".doc", ".docx", ".odt", ".zip")):
        return True
    blob = f"{href} {label}".lower()
    if "/files/upload/" in path:
        return True
    if "pdf" in blob and ("anexo" in blob or "edital" in blob or "chamada" in blob or "form" in blob):
        return True
    return False


def _attachment_filename(external_id: str, url: str, label: str, idx: int) -> str:
    path = urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext not in {".pdf", ".doc", ".docx", ".odt", ".zip"}:
        low = f"{url} {label}".lower()
        if ".docx" in low or "docx" in low:
            ext = ".docx"
        elif ".doc" in low:
            ext = ".doc"
        elif "pdf" in low:
            ext = ".pdf"
        else:
            ext = ".bin"
    # Preferir nome do arquivo na URL quando o texto do link e a propria URL.
    raw_stem = label or ""
    if raw_stem.lower().startswith("http") or len(raw_stem) > 90 or not raw_stem.strip():
        raw_stem = Path(unquote(path)).stem or f"anexo{idx}"
    stem = re.sub(r"[^\w\-]+", "_", raw_stem.lower(), flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("_")[:40] or f"anexo{idx}"
    prefix = external_id.replace("-", "_")
    return f"{prefix}_{stem}{ext}"
