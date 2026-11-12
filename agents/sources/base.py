"""Modelo comum e utilitarios para fontes de editais (alem da FINEP)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from agents.sources.finep import is_vigente, parse_finep_datetime

USER_AGENT = "recomendacao-fomento-agent/0.5 (+TCC; coletor educacional multi-fonte)"


@dataclass
class OpenCall:
    """Chamada/oportunidade normalizada (FAPESP, CNPq, Centelha, Embrapii, BNDES…)."""

    source: str
    external_id: str
    title: str
    detail_url: str
    situacao: str = "Aberta"
    published_at: str | None = None
    themes: list[str] = field(default_factory=list)
    opportunity_type: str | None = None
    region: str | None = None
    counterpart: str | None = None
    vigencia_inicio: str | None = None
    vigencia_fim: str | None = None
    prazo_proposta: str | None = None
    description_text: str = ""
    attachments: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def is_vigente_now(self, *, now: datetime | None = None) -> bool:
        return is_vigente(
            situacao=self.situacao,
            vigencia_inicio=self.vigencia_inicio,
            vigencia_fim=self.vigencia_fim,
            prazo_proposta=self.prazo_proposta,
            now=now,
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("raw", None)
        d["em_vigencia"] = self.is_vigente_now()
        d["chamada_id"] = self.external_id  # compat manifest/scraper FINEP
        return d


def http_client(*, timeout: float = 60.0, verify: bool = True) -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        },
        follow_redirects=True,
        timeout=timeout,
        verify=verify,
    )


def fetch_html(url: str, *, client: httpx.Client | None = None) -> str:
    """Baixa HTML. Em redes corporativas com proxy SSL, faz fallback verify=False."""
    if client is not None:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text

    try:
        with http_client(verify=True) as c:
            resp = c.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:  # noqa: BLE001 — proxy/SSL corporativo
        msg = str(exc).lower()
        if "ssl" not in msg and "certificate" not in msg and "certificado" not in msg:
            raise
        with http_client(verify=False) as c:
            resp = c.get(url)
            resp.raise_for_status()
            return resp.text


def slug_id(prefix: str, text: str, *, max_len: int = 72) -> str:
    base = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    base = re.sub(r"[-\s]+", "-", base).strip("-")[: max_len - len(prefix) - 1]
    if not base:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
        base = digest
    return f"{prefix}-{base}"


def parse_br_date(raw: str | None) -> datetime | None:
    """Converte dd/mm/aaaa (opcional hh:mm) para datetime UTC."""
    if not raw:
        return None
    text = str(raw).strip()
    # ja ISO?
    iso = parse_finep_datetime(text)
    if iso:
        return iso
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", text)
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hour = int(m.group(4) or 23)
    minute = int(m.group(5) or 59)
    try:
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except ValueError:
        return None


def br_date_to_iso(raw: str | None) -> str | None:
    dt = parse_br_date(raw)
    if not dt:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def absolute_url(base: str, href: str | None) -> str:
    if not href:
        return base
    return urljoin(base, href)


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def download_binary(
    url: str,
    dest: Path,
    *,
    min_cached_bytes: int = 800,
) -> tuple[Path, bool]:
    """Baixa arquivo binario (PDF/DOCX…). Retorna (path, is_new)."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= min_cached_bytes:
        return dest, False

    def _stream(verify: bool) -> None:
        with http_client(verify=verify) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".partial")
                with tmp.open("wb") as fh:
                    for chunk in resp.iter_bytes():
                        fh.write(chunk)
                tmp.replace(dest)

    try:
        _stream(True)
    except Exception as exc:  # noqa: BLE001 — proxy/SSL corporativo
        msg = str(exc).lower()
        if "ssl" not in msg and "certificate" not in msg and "certificado" not in msg:
            raise
        _stream(False)
    return dest, True
