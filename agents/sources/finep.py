"""Fonte FINEP — chamadas publicas, anexos e metadados ricos.

API publica Liferay Objects:
  GET /o/c/chamadapublicas
  GET /o/c/chamadapublicas/{id}?nestedFields=documentos

Pagina humana relacionada:
  https://www.finep.gov.br/oportunidades
  https://www.finep.gov.br/chamadas-publicas

Filtro padrao ``vigente``: situacao Aberta **e** janela temporal valida
(``prazoProposto`` / ``vigenciaInicio`` / ``vigenciaFim``). A API ainda lista
como Aberta chamadas com prazo de proposta ja vencido — essas sao excluidas.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urljoin

import httpx

FINEP_BASE = "https://www.finep.gov.br"
LIST_PATH = "/o/c/chamadapublicas"
USER_AGENT = "recomendacao-fomento-agent/0.2 (+TCC; coletor educacional)"

SituacaoFilter = Literal["vigente", "aberta", "todas", "encerrada"]

ROLE_PRIORITY = {
    "edital": 100,
    "regulamento": 90,
    "anexo": 50,
    "outro": 20,
    "faq": 5,
}


@dataclass
class FinepAttachment:
    role: str
    pdf_url: str
    pdf_name: str
    original_name: str
    legenda: str = ""


@dataclass
class FinepCall:
    """Uma chamada publica FINEP com metadados + anexos PDF."""

    chamada_id: int
    title: str
    situacao: str
    detail_url: str
    published_at: str | None = None
    themes: list[str] = field(default_factory=list)
    opportunity_type: str | None = None
    region: str | None = None
    target_audience: list[str] = field(default_factory=list)
    cooperation_type: str | None = None
    counterpart: str | None = None
    vigencia_inicio: str | None = None
    vigencia_fim: str | None = None
    prazo_proposta: str | None = None
    description_text: str = ""
    attachments: list[FinepAttachment] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def primary(self) -> FinepAttachment | None:
        if not self.attachments:
            return None
        return sorted(
            self.attachments,
            key=lambda a: ROLE_PRIORITY.get(a.role, 0),
            reverse=True,
        )[0]

    def is_vigente(self, *, now: datetime | None = None) -> bool:
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
        d["em_vigencia"] = self.is_vigente()
        return d


# Retrocompat: alias usado por testes/scraper antigo
@dataclass
class FinepDocument:
    chamada_id: int
    title: str
    situacao: str
    detail_url: str
    pdf_url: str
    pdf_name: str
    legenda: str = ""
    published_at: str | None = None
    themes: list[str] = field(default_factory=list)
    role: str = "edital"
    raw: dict[str, Any] = field(default_factory=dict)


def _headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


def _slug_filename(name: str, chamada_id: int, *, role: str = "") -> str:
    base = Path(name).name
    base = re.sub(r"[^\w\s.-]", "", base, flags=re.UNICODE)
    base = re.sub(r"\s+", "_", base).strip("._")
    if not base.lower().endswith(".pdf"):
        base = f"{base}.pdf"
    prefix = f"finep_{chamada_id}_"
    if role and role not in {"edital", "regulamento"}:
        prefix = f"finep_{chamada_id}_{role}_"
    return f"{prefix}{base}"[:180]


def _situacao_name(item: dict[str, Any]) -> str:
    situacao = item.get("situacao") or {}
    if isinstance(situacao, dict):
        return str(situacao.get("name") or situacao.get("key") or "")
    if isinstance(situacao, str):
        return situacao
    return ""


def parse_finep_datetime(raw: str | None) -> datetime | None:
    """Parse datas ISO da API FINEP (ex.: 2026-11-23T17:00:00.000Z)."""
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    try:
        if text.endswith("Z"):
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _is_open(item: dict[str, Any]) -> bool:
    return _situacao_name(item).lower().startswith("abert")


def is_vigente(
    *,
    situacao: str | None,
    vigencia_inicio: str | None = None,
    vigencia_fim: str | None = None,
    prazo_proposta: str | None = None,
    now: datetime | None = None,
) -> bool:
    """True se a chamada ainda aceita proposta / está em vigência.

    A API FINEP marca algumas chamadas como \"Aberta\" mesmo com prazoProposto
    já vencido. Aqui exigimos:
      - situacao Aberta (ou ausente, para metadados incompletos)
      - agora >= vigenciaInicio (se houver)
      - agora <= vigenciaFim (se houver)
      - agora <= prazoProposto (se houver)
    """
    ref = now or datetime.now(timezone.utc)
    name = (situacao or "").strip().lower()
    if name and not name.startswith("abert"):
        # Encerrada / Finalizada / etc.
        if "encerr" in name or "finaliz" in name or "cancel" in name:
            return False
        if name not in {"?", "desconhecido", "unknown"}:
            return False

    start = parse_finep_datetime(vigencia_inicio)
    end = parse_finep_datetime(vigencia_fim)
    prazo = parse_finep_datetime(prazo_proposta)

    if start and ref < start:
        return False
    if end and ref > end:
        return False
    if prazo and ref > prazo:
        return False
    return True


def is_item_vigente(item: dict[str, Any], *, now: datetime | None = None) -> bool:
    """Avalia item cru da API Liferay Objects."""
    return is_vigente(
        situacao=_situacao_name(item),
        vigencia_inicio=item.get("vigenciaInicio"),
        vigencia_fim=item.get("vigenciaFim"),
        prazo_proposta=item.get("prazoProposto"),
        now=now,
    )


def is_metadata_vigente(meta: dict[str, Any] | None, *, now: datetime | None = None) -> bool:
    """Avalia metadata persistida em edicts.metadata (seed/scraper)."""
    meta = meta or {}
    return is_vigente(
        situacao=str(meta.get("situacao") or "") or None,
        vigencia_inicio=meta.get("vigencia_inicio"),
        vigencia_fim=meta.get("vigencia_fim"),
        prazo_proposta=meta.get("prazo_proposta"),
        now=now,
    )


def _matches_situacao(item: dict[str, Any], filt: SituacaoFilter) -> bool:
    name = _situacao_name(item).lower()
    if filt == "todas":
        return True
    if filt == "aberta":
        # Apenas rótulo da API (pode incluir prazo já vencido).
        return name.startswith("abert")
    if filt == "vigente":
        return is_item_vigente(item)
    if filt == "encerrada":
        return "encerr" in name or "finaliz" in name
    return True


def _pick_name(val: Any) -> str | None:
    if isinstance(val, dict):
        return str(val.get("name") or val.get("key") or "") or None
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _theme_names(item: dict[str, Any]) -> list[str]:
    themes: list[str] = []
    for key in ("temaPrincipal", "tema"):
        val = item.get(key)
        if isinstance(val, list):
            for t in val:
                name = _pick_name(t) if not isinstance(t, str) else t
                if name:
                    themes.append(name)
        elif isinstance(val, dict):
            name = _pick_name(val)
            if name:
                themes.append(name)
        elif isinstance(val, str):
            themes.extend(p.strip() for p in val.split(";") if p.strip())

    for brief in item.get("taxonomyCategoryBriefs") or []:
        if isinstance(brief, dict) and brief.get("taxonomyCategoryName"):
            themes.append(str(brief["taxonomyCategoryName"]))

    seen: set[str] = set()
    out: list[str] = []
    for t in themes:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _audience(item: dict[str, Any]) -> list[str]:
    raw = item.get("publicoAlvo") or []
    out: list[str] = []
    if isinstance(raw, list):
        for x in raw:
            name = _pick_name(x) if not isinstance(x, str) else x
            if name:
                out.append(name)
    elif isinstance(raw, str) and raw.strip():
        out.append(raw.strip())
    return out


def _classify_role(label: str, legenda: str) -> str:
    blob = f"{label} {legenda}".lower()
    if "faq" in blob or "perguntas" in blob:
        return "faq"
    if "edital" in blob:
        return "edital"
    if "regulamento" in blob:
        return "regulamento"
    if "anexo" in blob or "instru" in blob or "manual" in blob:
        return "anexo"
    return "outro"


def _list_pdf_attachments(
    documentos: list[dict[str, Any]], chamada_id: int
) -> list[FinepAttachment]:
    out: list[FinepAttachment] = []
    seen_urls: set[str] = set()
    for doc in documentos or []:
        prop = doc.get("documentoProprietario") or {}
        link = prop.get("link") or {}
        href = link.get("href") or ""
        label = str(prop.get("name") or link.get("label") or "documento.pdf")
        legenda = str(doc.get("legenda") or "")
        if not href:
            continue
        if not label.lower().endswith(".pdf") and ".pdf" not in href.lower():
            continue
        url = urljoin(FINEP_BASE, href)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        role = _classify_role(label, legenda)
        out.append(
            FinepAttachment(
                role=role,
                pdf_url=url,
                pdf_name=_slug_filename(label, chamada_id, role=role),
                original_name=label,
                legenda=legenda,
            )
        )
    out.sort(key=lambda a: ROLE_PRIORITY.get(a.role, 0), reverse=True)
    return out


def _pick_pdf(documentos: list[dict[str, Any]]) -> tuple[str, str, str] | None:
    """Retrocompat testes: retorna (url, filename, legenda) do melhor PDF."""
    atts = _list_pdf_attachments(documentos, chamada_id=0)
    if not atts:
        return None
    # sem prefixo finep_0_ confuso — usar original para teste
    best = atts[0]
    return best.pdf_url, best.original_name, best.legenda


def _strip_html(html: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html or "")
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _build_call(item: dict[str, Any], documentos: list[dict[str, Any]]) -> FinepCall:
    chamada_id = int(item["id"])
    desc = str(item.get("descricaoRawText") or "").strip()
    if not desc and item.get("descricao"):
        desc = _strip_html(str(item.get("descricao")))
    return FinepCall(
        chamada_id=chamada_id,
        title=str(item.get("titulo") or f"FINEP {chamada_id}"),
        situacao=_situacao_name(item),
        detail_url=f"{FINEP_BASE}/e/chamada-publica/222684/{chamada_id}",
        published_at=item.get("dataDePublicacao"),
        themes=_theme_names(item),
        opportunity_type=_pick_name(item.get("tipoDeOportunidade")),
        region=_pick_name(item.get("regiao")),
        target_audience=_audience(item),
        cooperation_type=_pick_name(item.get("tipoCooperacao")),
        counterpart=_pick_name(item.get("contrapartida")),
        vigencia_inicio=item.get("vigenciaInicio"),
        vigencia_fim=item.get("vigenciaFim"),
        prazo_proposta=item.get("prazoProposto"),
        description_text=desc,
        attachments=_list_pdf_attachments(documentos, chamada_id),
        raw=item,
    )


class FinepSource:
    """Cliente da fonte FINEP (chamadas + anexos)."""

    def __init__(self, client: httpx.Client | None = None, timeout: float = 60.0) -> None:
        self._owns_client = client is None
        self.client = client or httpx.Client(
            headers=_headers(),
            follow_redirects=True,
            timeout=timeout,
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> FinepSource:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def list_calls(
        self,
        *,
        situacao: SituacaoFilter = "vigente",
        page_size: int = 50,
        max_pages: int = 200,
    ) -> list[dict[str, Any]]:
        """Lista chamadas da API publica.

        Padrao ``vigente``: situacao Aberta **e** prazo/janela de vigencia ainda validos.
        Use ``aberta`` apenas se quiser o rotulo bruto da FINEP (inclui prazo vencido).
        """
        items_out: list[dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            r = self.client.get(
                urljoin(FINEP_BASE, LIST_PATH),
                params={
                    "sort": "dataDePublicacao:desc",
                    "pageSize": page_size,
                    "page": page,
                },
            )
            r.raise_for_status()
            payload = r.json()
            items = payload.get("items") or []
            if not items:
                break
            items_out.extend(it for it in items if _matches_situacao(it, situacao))
            last = int(payload.get("lastPage") or page)
            if page >= last:
                break
        return items_out

    def list_open_calls(self, *, page_size: int = 50, max_pages: int = 200) -> list[dict[str, Any]]:
        """Alias historico: agora equivale a vigentes (nao so rotulo Aberta)."""
        return self.list_calls(situacao="vigente", page_size=page_size, max_pages=max_pages)

    def fetch_detail(self, chamada_id: int) -> dict[str, Any]:
        r = self.client.get(
            urljoin(FINEP_BASE, f"{LIST_PATH}/{chamada_id}"),
            params={"nestedFields": "documentos"},
        )
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, dict) else {}

    def fetch_documents(self, chamada_id: int) -> list[dict[str, Any]]:
        data = self.fetch_detail(chamada_id)
        docs = data.get("documentos") or []
        return docs if isinstance(docs, list) else []

    def collect_calls(
        self,
        *,
        limit: int | None = None,
        situacao: SituacaoFilter = "vigente",
        require_pdf: bool = True,
    ) -> list[FinepCall]:
        """Coleta chamadas. limit=None significa todas as que passarem no filtro."""
        results: list[FinepCall] = []
        for item in self.list_calls(situacao=situacao):
            if limit is not None and len(results) >= limit:
                break
            chamada_id = int(item["id"])
            detail = self.fetch_detail(chamada_id)
            # merge list item + detail (detail wins)
            merged = {**item, **detail}
            docs = detail.get("documentos") or []
            if not isinstance(docs, list):
                docs = []
            call = _build_call(merged, docs)
            # Revalida no detalhe (datas podem estar só no nested payload).
            if situacao == "vigente" and not call.is_vigente():
                continue
            if require_pdf and not call.attachments:
                continue
            results.append(call)
        return results

    def collect_pdf_targets(self, *, limit: int | None = None) -> list[FinepDocument]:
        """Retrocompat: um FinepDocument por chamada (PDF primario)."""
        out: list[FinepDocument] = []
        for call in self.collect_calls(limit=limit, situacao="vigente"):
            primary = call.primary
            if not primary:
                continue
            out.append(
                FinepDocument(
                    chamada_id=call.chamada_id,
                    title=call.title,
                    situacao=call.situacao,
                    detail_url=call.detail_url,
                    pdf_url=primary.pdf_url,
                    pdf_name=primary.pdf_name,
                    legenda=primary.legenda,
                    published_at=call.published_at,
                    themes=call.themes,
                    role=primary.role,
                    raw=call.raw,
                )
            )
        return out

    def download_attachment(
        self, att: FinepAttachment, dest_dir: Path
    ) -> tuple[Path, bool]:
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        path = dest_dir / att.pdf_name
        if path.exists() and path.stat().st_size > 1000:
            return path, False
        with self.client.stream("GET", att.pdf_url) as resp:
            resp.raise_for_status()
            tmp = path.with_suffix(".partial")
            with tmp.open("wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)
            tmp.replace(path)
        return path, True

    def download_pdf(self, doc: FinepDocument, dest_dir: Path) -> tuple[Path, bool]:
        att = FinepAttachment(
            role=doc.role or "edital",
            pdf_url=doc.pdf_url,
            pdf_name=doc.pdf_name,
            original_name=doc.pdf_name,
            legenda=doc.legenda,
        )
        return self.download_attachment(att, dest_dir)
