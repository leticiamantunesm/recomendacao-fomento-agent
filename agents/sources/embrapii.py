"""Fonte Embrapii — chamadas publicas (Transparencia) + areas de atuacao.

Portais:
  https://embrapii.org.br/transparencia/#chamadas
  https://embrapii.org.br/chamadas-publicas/...
  https://embrapii.org.br/areas-de-atuacao/
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from agents.sources.base import (
    OpenCall,
    absolute_url,
    clean_text,
    download_binary,
    fetch_html,
    slug_id,
)

EMBRAPII_TRANSPARENCIA_URL = "https://embrapii.org.br/transparencia/"
EMBRAPII_AREAS_URL = "https://embrapii.org.br/areas-de-atuacao/"
EMBRAPII_BASE = "https://embrapii.org.br"

_MACRO_AREAS = {
    "BIOTECNOLOGIA",
    "MATERIAIS E QUÍMICA",
    "MATERIAIS E QUIMICA",
    "MECÂNICA E MANUFATURA",
    "MECANICA E MANUFATURA",
    "TECNOLOGIA DA INFORMAÇÃO E COMUNICAÇÃO",
    "TECNOLOGIA DA INFORMACAO E COMUNICACAO",
    "TECNOLOGIAS APLICADAS",
}

_SKIP_FILE_PATTERNS = (
    "sharepoint.com",
    "teams.microsoft",
    "webinar",
)

_DOC_EXTS = (".pdf", ".doc", ".docx", ".odt", ".xlsx", ".xls", ".zip")


class EmbrapiiSource:
    def close(self) -> None:
        return None

    def __enter__(self) -> EmbrapiiSource:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def collect_calls(
        self,
        *,
        limit: int | None = None,
        only_open: bool = True,
        enrich_details: bool = True,
        include_areas: bool = True,
    ) -> list[OpenCall]:
        public = self._collect_from_transparencia()
        if only_open:
            public = [c for c in public if not c.situacao.lower().startswith("encerr")]
        public.sort(key=_call_sort_key)

        out: list[OpenCall] = []
        seen: set[str] = set()

        for call in public:
            key = call.detail_url.rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            if enrich_details and "/chamadas-publicas/" in call.detail_url:
                try:
                    self.enrich_call(call)
                except Exception as exc:  # noqa: BLE001
                    call.raw = {**(call.raw or {}), "enrich_error": str(exc)[:300]}
            out.append(call)
            if limit is not None and len(out) >= limit:
                return out

        if include_areas:
            for call in self._collect_areas_as_continuous():
                key = f"{call.external_id}:{call.title}".lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(call)
                if limit is not None and len(out) >= limit:
                    break
        return out

    def enrich_call(self, call: OpenCall) -> OpenCall:
        """Carrega pagina da chamada: texto + anexos (PDF/DOCX)."""
        html = fetch_html(call.detail_url)
        soup = BeautifulSoup(html, "html.parser")

        h1 = soup.find("h1")
        if h1:
            title = clean_text(h1.get_text(" ", strip=True))
            if title and len(title) > 10:
                call.title = title[:300]

        content = soup.select_one(".chamadas-publicas-content") or soup.select_one(
            "section.chamadas-publicas-interna"
        )
        if content is None:
            content = soup.select_one("main") or soup.body
        if content is None:
            return call

        text = _clean_detail_text(content.get_text("\n", strip=True))
        # Remove bloco lateral de filtro se veio junto.
        text = re.sub(
            r"(?is)\nFiltrar\nRecentes\nMais Lidos\n.*$",
            "",
            text,
        ).strip()
        if len(text) > 200:
            call.description_text = text[:50000]
        elif call.title:
            call.description_text = (
                f"{call.title}. Chamada pública Embrapii. Detalhes e documentos em "
                f"{call.detail_url}"
            )

        call.themes = _themes_from_title(call.title)
        call.attachments = _extract_attachments(soup, call.external_id, call.detail_url)
        call.raw = {
            **(call.raw or {}),
            "detail_chars": len(text),
            "attachment_count": len(call.attachments),
        }
        return call

    def download_attachment(self, att: dict, dest_dir: Path) -> tuple[Path, bool]:
        url = str(att.get("pdf_url") or att.get("url") or "")
        name = str(att.get("pdf_name") or "")
        if not url or not name:
            raise ValueError("anexo Embrapii sem pdf_url/pdf_name")
        return download_binary(url, Path(dest_dir) / name)

    def _collect_from_transparencia(self) -> list[OpenCall]:
        html = fetch_html(EMBRAPII_TRANSPARENCIA_URL)
        soup = BeautifulSoup(html, "html.parser")
        section = soup.find(id="chamadas") or soup.find(id="chamadas-publicas") or soup
        calls: list[OpenCall] = []
        seen_urls: set[str] = set()

        for a in section.find_all("a", href=True):
            href = a.get("href") or ""
            label = clean_text(a.get_text(" ", strip=True))
            if "/chamadas-publicas/" not in href.lower():
                continue
            url = absolute_url(EMBRAPII_BASE, href).split("#")[0].rstrip("/") + "/"
            # Prefer links "Ver documentos" ou titulo da chamada.
            title = _title_near_link(a)
            if not title:
                if label.lower() in {"ver documentos", "documentos"}:
                    continue
                title = label
            if len(title) < 15:
                continue
            if title.lower() in {"chamadas públicas", "chamadas publicas"}:
                continue
            key = url.lower()
            if key in seen_urls:
                continue
            seen_urls.add(key)

            situacao = _situacao_from_title(title)
            calls.append(
                OpenCall(
                    source="EMBRAPII",
                    external_id=embrapii_external_id(url, title),
                    title=title[:300],
                    detail_url=url,
                    situacao=situacao,
                    themes=_themes_from_title(title),
                    opportunity_type="Chamada pública Embrapii",
                    region="Brasil",
                    description_text=(
                        f"{title}. Documentos e detalhes em {url}"
                    ),
                    raw={"listing": "transparencia#chamadas"},
                )
            )
        return calls

    def _collect_areas_as_continuous(self) -> list[OpenCall]:
        """Areas/competencias = modalidades de atuacao em fluxo continuo."""
        html = fetch_html(EMBRAPII_AREAS_URL)
        soup = BeautifulSoup(html, "html.parser")
        options = [
            clean_text(o.get_text(" ", strip=True))
            for o in soup.find_all("option")
            if clean_text(o.get_text(" ", strip=True))
        ]
        skip = {"selecione", "competências tecnológicas", "competencias tecnologicas", ""}
        calls: list[OpenCall] = []
        for opt in options:
            if opt.lower() in skip:
                continue
            is_macro = opt.upper() in _MACRO_AREAS or opt.upper().replace("Á", "A").replace("Ç", "C") in {
                a.replace("Á", "A").replace("Ç", "C") for a in _MACRO_AREAS
            }
            kind = "Área Embrapii" if is_macro else "Competência tecnológica Embrapii"
            title = f"Embrapii — {opt}"
            calls.append(
                OpenCall(
                    source="EMBRAPII",
                    external_id=slug_id("embrapii-area", opt),
                    title=title[:300],
                    detail_url=EMBRAPII_AREAS_URL,
                    situacao="Aberta",
                    themes=[opt, "PD&I", "inovação industrial"],
                    opportunity_type=f"{kind} (fluxo contínuo)",
                    region="Brasil",
                    description_text=(
                        f"Modalidade/competência Embrapii: {opt}. "
                        "A Embrapii conecta empresas a Unidades e Centros de Competência "
                        "para projetos de PD&I com modelo de compartilhamento de recursos. "
                        f"Consulte áreas em {EMBRAPII_AREAS_URL}"
                    ),
                    raw={"competencia": opt, "macro": is_macro},
                )
            )
        return calls


def embrapii_external_id(url: str, title: str) -> str:
    m = re.search(r"/chamadas-publicas/([^/]+)/?", url or "", flags=re.I)
    if m:
        slug = re.sub(r"[^\w\-]+", "-", m.group(1).lower()).strip("-")[:72]
        return f"embrapii-{slug}"
    return slug_id("embrapii", title)


def _title_near_link(a) -> str | None:
    """Extrai titulo da chamada proximo ao link 'Ver documentos'."""
    label = clean_text(a.get_text(" ", strip=True))
    if label and label.lower() not in {"ver documentos", "documentos"} and len(label) > 15:
        return label

    parent = a.parent
    for _ in range(8):
        if parent is None:
            break
        for p in parent.find_all("p"):
            cand = clean_text(p.get_text(" ", strip=True))
            if cand and "ver documentos" not in cand.lower() and len(cand) > 15:
                return cand
        raw = clean_text(parent.get_text(" ", strip=True))
        cand = re.sub(r"(?i)ver documentos", "", raw).strip()
        cand = re.sub(r"\s+", " ", cand)
        if 15 < len(cand) < 240:
            return cand
        parent = parent.parent
    return None


def _situacao_from_title(title: str) -> str:
    if re.search(r"resultado|encerrad|finaliz|preliminar", title or "", flags=re.I):
        return "Encerrada"
    return "Aberta"


def _themes_from_title(title: str) -> list[str]:
    themes = ["inovação industrial", "EMBRAPII"]
    low = (title or "").lower()
    if "circular" in low:
        themes.append("economia circular")
    if "petrobras" in low or "energia" in low:
        themes.append("energia")
    if "centro de compet" in low:
        themes.append("centro de competência")
    if "unidade" in low:
        themes.append("unidades Embrapii")
    if "norte" in low:
        themes.append("região Norte")
    if "fapesp" in low:
        themes.append("FAPESP")
    if "capacit" in low or "maturidade" in low:
        themes.append("capacitação")
    return list(dict.fromkeys(themes))


def _call_sort_key(call: OpenCall) -> tuple[int, int, int, str]:
    blob = f"{call.title} {call.detail_url}"
    years = [int(y) for y in re.findall(r"(20\d{2})", blob)]
    year = max(years) if years else 0
    open_boost = 0 if call.situacao.lower().startswith("encerr") else 1
    low = (call.title or "").lower()
    # Publicas antes de internas; depois A-Z.
    if "interna" in low:
        kind = 2
    elif "resultado" in low or "preliminar" in low:
        kind = 3
    else:
        kind = 0
    return (-year, -open_boost, kind, low)


def _clean_detail_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text or "")
    lines = []
    for line in text.splitlines():
        low = line.strip().lower()
        if low in {"filtrar", "recentes", "mais lidos", "download"}:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _extract_attachments(soup, external_id: str, page_url: str) -> list[dict]:
    root = (
        soup.select_one(".chamadas-publicas-content")
        or soup.select_one("section.chamadas-publicas-interna")
        or soup
    )
    found: list[dict] = []
    seen: set[str] = set()
    idx = 0
    for a in root.find_all("a", href=True):
        href = absolute_url(page_url, a["href"])
        label = clean_text(a.get_text(" ", strip=True)) or unquote(
            Path(urlparse(href).path).name
        )
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
        role = "edital" if href.lower().endswith(".pdf") and idx == 1 else "anexo"
        # Prefer PDF da propria chamada como edital
        if "chamada" in Path(urlparse(href).path).name.lower() and href.lower().endswith(".pdf"):
            role = "edital"
        found.append(
            {
                "role": role,
                "pdf_url": href,
                "pdf_name": pdf_name,
                "original_name": label[:200] or pdf_name,
                "legenda": label[:200],
            }
        )
    # Reordenar: editais PDF primeiro
    found.sort(key=lambda a: (0 if a["role"] == "edital" else 1, a["pdf_name"]))
    return found


def _is_noise_file(href: str, label: str) -> bool:
    blob = f"{href} {label}".lower()
    return any(p in blob for p in _SKIP_FILE_PATTERNS)


def _is_document_href(href: str, label: str) -> bool:
    path = urlparse(href).path.lower()
    if path.endswith(_DOC_EXTS):
        return True
    host = urlparse(href).netloc.lower()
    if "storage.googleapis.com" in host and "uploads-site-embrapii" in href.lower():
        return path.endswith(_DOC_EXTS) or "pdf" in path or "doc" in path
    if "/wp-content/uploads/" in path and path.endswith(_DOC_EXTS):
        return True
    return False


def _attachment_filename(external_id: str, url: str, label: str, idx: int) -> str:
    path = urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext not in _DOC_EXTS:
        low = f"{url} {label}".lower()
        if ".docx" in low:
            ext = ".docx"
        elif ".xlsx" in low:
            ext = ".xlsx"
        elif ".pdf" in low:
            ext = ".pdf"
        else:
            ext = ".bin"
    raw_stem = label or ""
    if (
        raw_stem.lower() in {"download", "ver documento", "ver documentos"}
        or raw_stem.lower().startswith("http")
        or len(raw_stem) > 90
        or not raw_stem.strip()
    ):
        raw_stem = Path(unquote(path)).stem or f"anexo{idx}"
        # GCS often prefixes uuid-
        raw_stem = re.sub(
            r"^[0-9a-f]{8}-",
            "",
            raw_stem,
            flags=re.I,
        )
    stem = re.sub(r"[^\w\-]+", "_", raw_stem.lower(), flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("_")[:50] or f"anexo{idx}"
    # external_id can be long; keep prefix short
    prefix = external_id.replace("-", "_")[:40]
    return f"{prefix}_{stem}{ext}"
