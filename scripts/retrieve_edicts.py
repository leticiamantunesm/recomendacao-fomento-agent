"""CLI — Retrieval Agent híbrido (T-030).

Uso:
  python -m scripts.retrieve_edicts --query "startup inovacao digital IA"
  python -m scripts.retrieve_edicts --query "..." --agency FINEP --k 3
  python -m scripts.retrieve_edicts --from-edict finep-986129 --k 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import text

from agents.retrieval_agent import CompanyProfile, ProjectQuery, RetrievalAgent
from app.config import ROOT_DIR
from db.session import dispose_engine, session_scope


async def _load_edict_text(external_id: str) -> tuple[str, str]:
    async with session_scope() as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT title, left(raw_text, 8000) AS raw_text
                    FROM edicts
                    WHERE external_id = :eid
                    """
                ),
                {"eid": external_id},
            )
        ).mappings().first()
    await dispose_engine()
    if not row:
        raise SystemExit(f"Edital não encontrado: {external_id}")
    return str(row["title"]), str(row["raw_text"] or "")


async def _run(args: argparse.Namespace) -> int:
    if args.from_edict:
        title, body = await _load_edict_text(args.from_edict)
        project = ProjectQuery(title=f"Projeto alinhado a {title}", text=body)
    else:
        project = ProjectQuery(title=args.title or "Consulta avulsa", text=args.query)

    areas = [a.strip() for a in (args.areas or "").split(";") if a.strip()]
    company = CompanyProfile(
        name=args.company,
        size=args.size,
        trl=args.trl,
        areas=areas,
    )

    agent = RetrievalAgent()
    result = await agent.retrieve(
        project,
        company,
        k=args.k,
        agency=args.agency,
        year=args.year,
        require_area_overlap=args.require_area_overlap,
        enforce_trl=args.enforce_trl,
        enforce_size=args.enforce_size,
    )

    print(f"Query: {result.query_title}")
    print(f"Backend embeddings: {result.backend}")
    print(f"Candidatos (apos filtro SQL): {result.candidate_count}")
    print(f"Filtros: {json.dumps(result.filters_applied, ensure_ascii=False)}")
    print()
    for i, m in enumerate(result.matches, 1):
        print(f"{i}. [{m.similarity:.3f}] {m.external_id} — {m.title}")
        print(f"   agency={m.agency} year={m.year} dist={m.distance:.4f}")
        for reason in m.reasons:
            print(f"   - {reason}")
        if m.url:
            print(f"   url: {m.url}")
        print()

    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = ROOT_DIR / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON salvo em {out}")

    return 0 if result.matches else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieval Agent (busca híbrida)")
    parser.add_argument("--query", type=str, default="", help="Texto do projeto/consulta")
    parser.add_argument("--title", type=str, default=None, help="Título do projeto")
    parser.add_argument("--from-edict", type=str, default=None, help="Usa texto de um edict como query")
    parser.add_argument("--company", type=str, default="Empresa Demo TCC")
    parser.add_argument("--size", type=str, default="EPP")
    parser.add_argument("--trl", type=int, default=5)
    parser.add_argument("--areas", type=str, default="inovação;tecnologias digitais")
    parser.add_argument("--agency", type=str, default=None)
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--require-area-overlap", action="store_true")
    parser.add_argument("--enforce-trl", action="store_true")
    parser.add_argument("--enforce-size", action="store_true")
    parser.add_argument("--out", type=str, default="data/outputs/retrieval_last.json")
    args = parser.parse_args()

    if not args.query and not args.from_edict:
        parser.error("Informe --query ou --from-edict")

    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
