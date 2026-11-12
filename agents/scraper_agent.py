"""Agente Coletor — FINEP + FAPESP + CNPq + Centelha + Embrapii + BNDES."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.sources import ALL_SOURCE_NAMES, collect_html_source
from agents.sources.base import OpenCall, download_binary
from agents.sources.finep import FinepCall, FinepSource, SituacaoFilter
from app.config import ROOT_DIR, get_settings
from scripts.extract_pdfs import extract_pdf, slugify

MANIFEST_PATH = ROOT_DIR / "data" / "corpus_manifest.csv"
COLLECT_LOG_PATH = ROOT_DIR / "data" / "outputs" / "collect_log.json"
FINEP_META_DIR = ROOT_DIR / "data" / "outputs" / "finep_metadata"
CALLS_META_DIR = ROOT_DIR / "data" / "outputs" / "calls_metadata"


@dataclass
class CollectResult:
    source: str
    downloaded: list[str] = field(default_factory=list)
    cached: list[str] = field(default_factory=list)
    skipped_no_pdf: int = 0
    errors: list[str] = field(default_factory=list)
    targets: list[dict[str, Any]] = field(default_factory=list)
    calls: int = 0

    @property
    def ok_count(self) -> int:
        return len(self.downloaded) + len(self.cached) + len(self.targets)


class ScraperAgent:
    """Orquestra coleta multi-fonte de editais/oportunidades."""

    def __init__(self, raw_pdfs_dir: Path | None = None) -> None:
        settings = get_settings()
        self.raw_pdfs_dir = raw_pdfs_dir or settings.raw_pdfs_dir
        self.texts_dir = settings.texts_dir

    def collect(
        self,
        sources: list[str] | None = None,
        *,
        limit: int | None = None,
        situacao: SituacaoFilter = "vigente",
        download_anexos: bool = True,
        replace_manifest: bool = False,
        extract_texts: bool = False,
    ) -> CollectResult:
        names = [s.strip().lower() for s in (sources or ["finep"]) if s.strip()]
        if not names:
            names = ["finep"]
        unknown = [n for n in names if n not in ALL_SOURCE_NAMES]
        if unknown:
            raise ValueError(f"Fontes desconhecidas: {unknown}. Validas: {ALL_SOURCE_NAMES}")

        merged = CollectResult(source="+".join(n.upper() for n in names))
        all_targets: list[dict[str, Any]] = []

        for name in names:
            if name == "finep":
                part = self.collect_finep(
                    limit=limit,
                    situacao=situacao,
                    download_anexos=download_anexos,
                    finep_only_manifest=False,
                    extract_texts=extract_texts,
                    write_log=False,
                )
            else:
                part = self.collect_html_portal(
                    name,
                    limit=limit,
                    download_anexos=download_anexos,
                    extract_texts=extract_texts,
                    write_log=False,
                )
            merged.calls += part.calls
            merged.downloaded.extend(part.downloaded)
            merged.cached.extend(part.cached)
            merged.errors.extend(part.errors)
            all_targets.extend(part.targets)

        merged.targets = all_targets
        if replace_manifest:
            _rewrite_manifest(all_targets)
        else:
            for t in all_targets:
                _upsert_manifest_from_target(t)
        _write_collect_log(merged)
        return merged

    def collect_finep(
        self,
        *,
        limit: int | None = None,
        situacao: SituacaoFilter = "vigente",
        download_anexos: bool = True,
        finep_only_manifest: bool = True,
        extract_texts: bool = False,
        write_log: bool = True,
    ) -> CollectResult:
        result = CollectResult(source="FINEP")
        with FinepSource() as source:
            try:
                calls = source.collect_calls(limit=limit, situacao=situacao, require_pdf=True)
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"listagem FINEP falhou: {exc}")
                return result

            result.calls = len(calls)
            for call in calls:
                payload = call.to_dict()
                payload["source"] = "FINEP"
                payload["external_id"] = f"finep-{call.chamada_id}"
                result.targets.append(payload)
                try:
                    self._persist_finep_call(
                        source,
                        call,
                        result,
                        download_anexos=download_anexos,
                        extract_texts=extract_texts,
                    )
                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"{call.chamada_id}: {exc}")

        if finep_only_manifest:
            _rewrite_manifest(result.targets)
        if write_log:
            _write_collect_log(result)
        return result

    def collect_html_portal(
        self,
        source_name: str,
        *,
        limit: int | None = None,
        only_open: bool = True,
        download_anexos: bool = True,
        extract_texts: bool = False,
        write_log: bool = True,
    ) -> CollectResult:
        label = source_name.upper()
        result = CollectResult(source=label)
        try:
            calls = collect_html_source(source_name, limit=limit, only_open=only_open)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"listagem {label} falhou: {exc}")
            return result

        result.calls = len(calls)
        for call in calls:
            try:
                self._persist_open_call(
                    call,
                    result,
                    download_anexos=download_anexos,
                    extract_texts=extract_texts,
                )
                result.targets.append(call.to_dict())
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{call.external_id}: {exc}")
                result.targets.append(call.to_dict())

        if write_log:
            _write_collect_log(result)
        return result

    def _persist_finep_call(
        self,
        source: FinepSource,
        call: FinepCall,
        result: CollectResult,
        *,
        download_anexos: bool,
        extract_texts: bool,
    ) -> None:
        FINEP_META_DIR.mkdir(parents=True, exist_ok=True)
        CALLS_META_DIR.mkdir(parents=True, exist_ok=True)
        payload = call.to_dict()
        payload["source"] = "FINEP"
        payload["external_id"] = f"finep-{call.chamada_id}"
        (FINEP_META_DIR / f"{call.chamada_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (CALLS_META_DIR / f"finep-{call.chamada_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        atts = call.attachments if download_anexos else ([call.primary] if call.primary else [])
        for att in atts:
            if att is None:
                continue
            path, is_new = source.download_attachment(att, self.raw_pdfs_dir)
            rel = str(Path(path).relative_to(ROOT_DIR))
            if is_new:
                result.downloaded.append(rel)
            else:
                result.cached.append(rel)
            if extract_texts:
                text, _pages, n_chars = extract_pdf(path)
                self.texts_dir.mkdir(parents=True, exist_ok=True)
                out = self.texts_dir / f"{slugify(path.name)}.txt"
                out.write_text(text, encoding="utf-8")
                if n_chars < 500:
                    result.errors.append(f"texto fraco: {path.name} ({n_chars} chars)")

    def _persist_open_call(
        self,
        call: OpenCall,
        result: CollectResult,
        *,
        download_anexos: bool = True,
        extract_texts: bool = False,
    ) -> None:
        CALLS_META_DIR.mkdir(parents=True, exist_ok=True)
        self.texts_dir.mkdir(parents=True, exist_ok=True)
        self.raw_pdfs_dir.mkdir(parents=True, exist_ok=True)

        if download_anexos and call.attachments:
            kept: list[dict[str, Any]] = []
            for att in call.attachments:
                if not isinstance(att, dict):
                    continue
                url = str(att.get("pdf_url") or att.get("url") or "")
                name = str(att.get("pdf_name") or "")
                if not url or not name:
                    continue
                try:
                    path, is_new = download_binary(url, self.raw_pdfs_dir / name)
                    rel = str(path.relative_to(ROOT_DIR))
                    if is_new:
                        result.downloaded.append(rel)
                    else:
                        result.cached.append(rel)
                    if extract_texts and path.suffix.lower() == ".pdf":
                        text, _pages, n_chars = extract_pdf(path)
                        out = self.texts_dir / f"{slugify(path.name)}.txt"
                        out.write_text(text, encoding="utf-8")
                        if n_chars < 500:
                            result.errors.append(f"texto fraco: {path.name} ({n_chars} chars)")
                    kept.append(att)
                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"{call.external_id} anexo {name or url}: {exc}")
            call.attachments = kept

        payload = call.to_dict()
        meta_path = CALLS_META_DIR / f"{call.external_id}.json"
        meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        result.cached.append(str(meta_path.relative_to(ROOT_DIR)))

        text_name = f"{slugify(call.external_id)}.txt"
        text_path = self.texts_dir / text_name
        body = (call.description_text or call.title or "").strip()
        if body:
            text_path.write_text(body, encoding="utf-8")
            result.downloaded.append(str(text_path.relative_to(ROOT_DIR)))


def _year_from(published_at: str | None) -> str:
    if published_at and len(str(published_at)) >= 4:
        return str(published_at)[:4]
    return str(datetime.now(timezone.utc).year)


def _manifest_fieldnames() -> list[str]:
    return [
        "id",
        "filename",
        "title",
        "doc_type",
        "agency",
        "year",
        "areas",
        "source_url",
        "language",
        "notes",
        "status",
        "opportunity_type",
        "region",
        "vigencia_fim",
        "prazo_proposta",
        "attachments",
        "situacao",
    ]


def _row_from_target(t: dict[str, Any]) -> dict[str, str]:
    source = str(t.get("source") or "FINEP").upper()
    external_id = str(t.get("external_id") or "")
    if not external_id and t.get("chamada_id"):
        # FINEP legado / OpenCall compat
        cid = t.get("chamada_id")
        external_id = str(cid) if str(cid).startswith(("finep-", "fapesp-", "cnpq-", "centelha-", "embrapii-", "bndes-")) else f"finep-{cid}"

    attachments = t.get("attachments") or []
    primary_name = ""
    att_names: list[str] = []
    if attachments and isinstance(attachments, list) and attachments and isinstance(attachments[0], dict):
        from agents.sources.finep import ROLE_PRIORITY

        ordered = sorted(
            attachments,
            key=lambda a: ROLE_PRIORITY.get(a.get("role") or "", 0),
            reverse=True,
        )
        pdfs = [
            a
            for a in ordered
            if str(a.get("pdf_name") or "").lower().endswith(".pdf")
        ]
        primary = (pdfs[0] if pdfs else ordered[0]) if ordered else {}
        primary_name = str(primary.get("pdf_name") or "")
        att_names = [str(a.get("pdf_name") or "") for a in ordered if a.get("pdf_name")]
    if not primary_name:
        # Texto da chamada (HTML enriquecido) como documento primario
        primary_name = f"{slugify(external_id)}.txt" if external_id else ""

    themes = t.get("themes") or []
    areas = ";".join(themes) if themes else f"inovação;{source}"
    notes_parts = [
        f"Coletado automaticamente. situacao={t.get('situacao') or ''}",
        f"tipo={t.get('opportunity_type') or ''}",
        f"fonte={source}",
    ]
    return {
        "id": external_id,
        "filename": primary_name,
        "title": str(t.get("title") or ""),
        "doc_type": "edital" if source == "FINEP" else "oportunidade",
        "agency": source if source != "FINEP" else "FINEP",
        "year": _year_from(t.get("published_at")),
        "areas": areas,
        "source_url": str(t.get("detail_url") or ""),
        "language": "pt-BR",
        "notes": "; ".join(notes_parts),
        "status": "collected",
        "opportunity_type": str(t.get("opportunity_type") or ""),
        "region": str(t.get("region") or ""),
        "vigencia_fim": str(t.get("vigencia_fim") or ""),
        "prazo_proposta": str(t.get("prazo_proposta") or ""),
        "attachments": ";".join(att_names),
        "situacao": str(t.get("situacao") or ""),
    }


def _rewrite_manifest(targets: list[dict[str, Any]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = [_row_from_target(t) for t in targets if t.get("external_id") or t.get("chamada_id")]
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_manifest_fieldnames())
        writer.writeheader()
        writer.writerows(rows)


def _upsert_manifest_from_target(t: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _manifest_fieldnames()
    rows: list[dict[str, str]] = []
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    new_row = _row_from_target(t)
    if not new_row.get("id"):
        return
    updated = False
    for i, row in enumerate(rows):
        if row.get("id") == new_row["id"]:
            rows[i] = {**{k: row.get(k, "") for k in fieldnames}, **new_row}
            updated = True
            break
    if not updated:
        rows.append(new_row)
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_collect_log(result: CollectResult) -> None:
    COLLECT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Mantem alias legado.
    legacy = ROOT_DIR / "data" / "outputs" / "finep_collect_log.json"
    payload = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": result.source,
        "calls": result.calls,
        "downloaded": result.downloaded,
        "cached": result.cached,
        "errors": result.errors,
        "targets": result.targets,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    COLLECT_LOG_PATH.write_text(text, encoding="utf-8")
    if result.source.upper() == "FINEP" or result.source.upper().startswith("FINEP"):
        legacy.write_text(text, encoding="utf-8")
