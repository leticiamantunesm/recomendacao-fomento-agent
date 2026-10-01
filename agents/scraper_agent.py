"""Agente Coletor — busca editais FINEP (chamadas + anexos + metadados)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.sources.finep import FinepCall, FinepSource, SituacaoFilter
from app.config import ROOT_DIR, get_settings
from scripts.extract_pdfs import extract_pdf

MANIFEST_PATH = ROOT_DIR / "data" / "corpus_manifest.csv"
COLLECT_LOG_PATH = ROOT_DIR / "data" / "outputs" / "finep_collect_log.json"
META_DIR = ROOT_DIR / "data" / "outputs" / "finep_metadata"


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
        return len(self.downloaded) + len(self.cached)


class ScraperAgent:
    """Orquestra coleta FINEP ampliada."""

    def __init__(self, raw_pdfs_dir: Path | None = None) -> None:
        settings = get_settings()
        self.raw_pdfs_dir = raw_pdfs_dir or settings.raw_pdfs_dir
        self.texts_dir = settings.texts_dir

    def collect_finep(
        self,
        *,
        limit: int | None = None,
        situacao: SituacaoFilter = "aberta",
        download_anexos: bool = True,
        finep_only_manifest: bool = True,
        extract_texts: bool = False,
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
                result.targets.append(call.to_dict())
                try:
                    self._persist_call(
                        source,
                        call,
                        result,
                        download_anexos=download_anexos,
                        extract_texts=extract_texts,
                    )
                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"{call.chamada_id}: {exc}")

        if finep_only_manifest:
            _rewrite_manifest_finep_only(calls_meta=result.targets)
        else:
            for t in result.targets:
                _upsert_manifest_from_target(t)

        _write_collect_log(result)
        return result

    def _persist_call(
        self,
        source: FinepSource,
        call: FinepCall,
        result: CollectResult,
        *,
        download_anexos: bool,
        extract_texts: bool,
    ) -> None:
        META_DIR.mkdir(parents=True, exist_ok=True)
        meta_path = META_DIR / f"{call.chamada_id}.json"
        meta_path.write_text(
            json.dumps(call.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        atts = call.attachments if download_anexos else ([call.primary] if call.primary else [])
        saved_files: list[str] = []
        for att in atts:
            if att is None:
                continue
            path, is_new = source.download_attachment(att, self.raw_pdfs_dir)
            rel = str(Path(path).relative_to(ROOT_DIR))
            saved_files.append(Path(path).name)
            if is_new:
                result.downloaded.append(rel)
            else:
                result.cached.append(rel)
            if extract_texts:
                text, _pages, n_chars = extract_pdf(path)
                self.texts_dir.mkdir(parents=True, exist_ok=True)
                from scripts.extract_pdfs import slugify

                out = self.texts_dir / f"{slugify(path.name)}.txt"
                out.write_text(text, encoding="utf-8")
                if n_chars < 500:
                    result.errors.append(f"texto fraco: {path.name} ({n_chars} chars)")


def _year_from(published_at: str | None) -> str:
    if published_at and len(str(published_at)) >= 4:
        return str(published_at)[:4]
    return ""


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
    primary_name = ""
    att_names: list[str] = []
    for att in t.get("attachments") or []:
        name = att.get("pdf_name") or ""
        if name:
            att_names.append(name)
        if not primary_name and att.get("role") in {"edital", "regulamento", "anexo", "outro", "faq"}:
            # prefer first (already sorted by role priority in FinepCall.to_dict order)
            pass
    attachments = t.get("attachments") or []
    if attachments:
        # same sort as FinepCall.primary
        from agents.sources.finep import ROLE_PRIORITY

        ordered = sorted(
            attachments,
            key=lambda a: ROLE_PRIORITY.get(a.get("role") or "", 0),
            reverse=True,
        )
        primary_name = ordered[0].get("pdf_name") or ""
        att_names = [a.get("pdf_name") or "" for a in ordered if a.get("pdf_name")]

    themes = t.get("themes") or []
    areas = ";".join(themes) if themes else "inovação;FINEP"
    notes_parts = [
        f"Coletado automaticamente. situacao={t.get('situacao') or ''}",
        f"tipo={t.get('opportunity_type') or ''}",
        f"anexos={len(attachments)}",
    ]
    return {
        "id": f"finep-{t.get('chamada_id')}",
        "filename": primary_name,
        "title": str(t.get("title") or ""),
        "doc_type": "edital",
        "agency": "FINEP",
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


def _rewrite_manifest_finep_only(*, calls_meta: list[dict[str, Any]]) -> None:
    """Reescreve o manifest apenas com chamadas FINEP coletadas (corpus fresco)."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = [_row_from_target(t) for t in calls_meta if t.get("chamada_id")]
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
    payload = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": result.source,
        "calls": result.calls,
        "downloaded": result.downloaded,
        "cached": result.cached,
        "errors": result.errors,
        "targets": result.targets,
    }
    COLLECT_LOG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
