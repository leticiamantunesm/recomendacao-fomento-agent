"""Seed do corpus no Neon (edicts) — prioriza FINEP fresca.

Uso:
  python -m scripts.seed_corpus
  python -m scripts.seed_corpus --agency FINEP --purge-other
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
from pathlib import Path

from sqlalchemy import delete, select, text

from app.config import ROOT_DIR, get_settings
from db.models import Company, Edict
from db.session import dispose_engine, session_scope
from scripts.extract_pdfs import slugify

MANIFEST = ROOT_DIR / "data" / "corpus_manifest.csv"
META_DIR = ROOT_DIR / "data" / "outputs" / "finep_metadata"


def _split_areas(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[;|,]", raw)
    return [p.strip() for p in parts if p.strip()]


def _find_text_for_pdf(texts_dir: Path, pdf_filename: str) -> Path | None:
    if not pdf_filename:
        return None
    expected = texts_dir / f"{slugify(pdf_filename)}.txt"
    if expected.exists():
        return expected
    stem = Path(pdf_filename).stem.lower()
    m = re.search(r"finep[_\-]?(\d+)", stem, flags=re.I)
    if m:
        for path in texts_dir.glob(f"finep_{m.group(1)}_*.txt"):
            return path
    slug = slugify(pdf_filename)
    for path in texts_dir.glob("*.txt"):
        if path.stem == slug or slug in path.stem or path.stem in slug:
            return path
    return None


def _load_finep_meta(external_id: str) -> dict | None:
    m = re.match(r"finep-(\d+)$", external_id)
    if not m:
        return None
    path = META_DIR / f"{m.group(1)}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _compose_raw_text(
    *,
    texts_dir: Path,
    filename: str,
    attachments: str,
    finep_meta: dict | None,
) -> tuple[str | None, list[str]]:
    """Junta descricao da API + PDF primario + anexos extraidos."""
    parts: list[str] = []
    used: list[str] = []

    if finep_meta and finep_meta.get("description_text"):
        parts.append("# Descricao oficial (FINEP)\n" + str(finep_meta["description_text"]))
        used.append("api:descricao")

    files: list[str] = []
    if filename:
        files.append(filename)
    for name in (attachments or "").split(";"):
        name = name.strip()
        if name and name not in files:
            files.append(name)

    for name in files:
        text_path = _find_text_for_pdf(texts_dir, name)
        if text_path and text_path.exists():
            body = text_path.read_text(encoding="utf-8").strip()
            if body:
                parts.append(f"# Documento: {name}\n{body}")
                used.append(str(text_path.relative_to(ROOT_DIR)))

    if not parts:
        return None, used
    return "\n\n---\n\n".join(parts), used


async def seed(*, agency: str | None, purge_other: bool) -> None:
    settings = get_settings()
    if "SUA_SENHA" in settings.database_url or "ep-XXXX" in settings.database_url:
        raise SystemExit(
            "DATABASE_URL com placeholder. Configure o .env com a URL real do Neon."
        )
    if not MANIFEST.exists():
        raise SystemExit(f"Manifest nao encontrado: {MANIFEST}")

    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    if agency:
        rows = [r for r in rows if (r.get("agency") or "").upper() == agency.upper()]
    texts_dir = settings.texts_dir

    async with session_scope() as session:
        existing = await session.scalar(select(Company).where(Company.name == "Empresa Demo TCC"))
        if existing is None:
            company = Company(
                name="Empresa Demo TCC",
                size="EPP",
                trl=5,
                areas=["inovação", "tecnologias digitais"],
            )
            session.add(company)
            print("+ company: Empresa Demo TCC")
        else:
            print("= company ja existe: Empresa Demo TCC")

        if purge_other:
            if agency and agency.upper() == "FINEP":
                from sqlalchemy import and_

                res = await session.execute(
                    delete(Edict).where(
                        ~and_(
                            Edict.agency.ilike("FINEP"),
                            Edict.external_id.like("finep-%"),
                        )
                    )
                )
                print(f"- purge non-FINEP edicts: {res.rowcount}")
            else:
                print("! --purge-other so faz sentido com --agency FINEP; ignorado")

        upserted = 0
        skipped = 0
        keep_ids: set[str] = set()

        for row in rows:
            external_id = (row.get("id") or "").strip()
            filename = (row.get("filename") or "").strip()
            title = (row.get("title") or filename or external_id).strip()
            if not external_id:
                skipped += 1
                continue
            keep_ids.add(external_id)

            finep_meta = _load_finep_meta(external_id)
            raw_text, text_sources = _compose_raw_text(
                texts_dir=texts_dir,
                filename=filename,
                attachments=row.get("attachments") or "",
                finep_meta=finep_meta,
            )
            if not raw_text or len(raw_text) < 500:
                print(f"! texto fraco/ausente para {external_id} — grava metadados mesmo assim")

            year_raw = (row.get("year") or "").strip()
            year = int(year_raw) if year_raw.isdigit() else None
            agency_val = (row.get("agency") or "").strip() or None
            source = "FINEP" if external_id.startswith("finep-") else (agency_val or "manual")
            areas = _split_areas(row.get("areas"))
            if finep_meta and finep_meta.get("themes"):
                areas = list(dict.fromkeys([*areas, *finep_meta["themes"]]))
            url = (row.get("source_url") or "").strip() or None
            file_path = f"data/raw_pdfs/{filename}" if filename else None

            metadata = {
                "doc_type": row.get("doc_type"),
                "notes": row.get("notes"),
                "language": row.get("language"),
                "status": row.get("status"),
                "opportunity_type": row.get("opportunity_type")
                or (finep_meta or {}).get("opportunity_type"),
                "region": row.get("region") or (finep_meta or {}).get("region"),
                "vigencia_inicio": (finep_meta or {}).get("vigencia_inicio"),
                "vigencia_fim": row.get("vigencia_fim")
                or (finep_meta or {}).get("vigencia_fim"),
                "prazo_proposta": row.get("prazo_proposta")
                or (finep_meta or {}).get("prazo_proposta"),
                "situacao": row.get("situacao") or (finep_meta or {}).get("situacao"),
                "target_audience": (finep_meta or {}).get("target_audience"),
                "cooperation_type": (finep_meta or {}).get("cooperation_type"),
                "counterpart": (finep_meta or {}).get("counterpart"),
                "attachments": row.get("attachments"),
                "text_sources": text_sources,
                "finep_meta_file": f"data/outputs/finep_metadata/{external_id.split('-')[-1]}.json"
                if external_id.startswith("finep-")
                else None,
            }

            edict = await session.scalar(select(Edict).where(Edict.external_id == external_id))
            if edict is None:
                edict = Edict(external_id=external_id, title=title)
                session.add(edict)
                action = "+"
            else:
                action = "~"

            edict.source = source
            edict.title = title
            edict.agency = agency_val
            edict.year = year
            edict.areas = areas
            edict.raw_text = raw_text
            edict.file_path = file_path
            edict.url = url
            edict.metadata_ = metadata
            upserted += 1
            chars = len(raw_text) if raw_text else 0
            print(f"{action} edict {external_id}: {title[:60]}... chars={chars}")

        # remove FINEP orfas que nao estao no manifest atual (quando agency=FINEP)
        if agency and agency.upper() == "FINEP" and keep_ids:
            orphans = (
                await session.scalars(
                    select(Edict).where(
                        Edict.external_id.like("finep-%"),
                        ~Edict.external_id.in_(list(keep_ids)),
                    )
                )
            ).all()
            for o in orphans:
                print(f"- remove orphan {o.external_id}")
                await session.delete(o)

        await session.commit()
        count = await session.scalar(text("SELECT count(*) FROM edicts"))
        finep_count = await session.scalar(
            text("SELECT count(*) FROM edicts WHERE agency ILIKE 'FINEP'")
        )
        print(f"\nSeed OK — upserts={upserted} skipped={skipped} total={count} finep={finep_count}")

    await dispose_engine()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed corpus → Neon")
    parser.add_argument("--agency", default=None, help="Filtra manifest (ex.: FINEP)")
    parser.add_argument(
        "--purge-other",
        action="store_true",
        help="Com --agency FINEP, remove editais nao-FINEP do banco",
    )
    args = parser.parse_args()
    try:
        asyncio.run(seed(agency=args.agency, purge_other=args.purge_other))
    except SystemExit as exc:
        print(exc)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Falha no seed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
