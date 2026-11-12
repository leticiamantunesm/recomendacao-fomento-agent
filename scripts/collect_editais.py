"""CLI — coleta automatica multi-fonte (FINEP + FAPESP + CNPq + Centelha + Embrapii + BNDES).

Uso:
  python -m scripts.collect_editais --source all --replace-manifest
  python -m scripts.collect_editais --source finep,fapesp,cnpq --limit 20
  python -m scripts.collect_editais --source finep --situacao vigente --anexos --extract
"""

from __future__ import annotations

import argparse

from agents.scraper_agent import ScraperAgent
from agents.sources import ALL_SOURCE_NAMES


def _parse_sources(raw: str) -> list[str]:
    text = (raw or "finep").strip().lower()
    if text in {"all", "*"}:
        return list(ALL_SOURCE_NAMES)
    parts = [p.strip().lower() for p in text.split(",") if p.strip()]
    return parts or ["finep"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agente Coletor multi-fonte de editais")
    parser.add_argument(
        "--source",
        default="finep",
        help=(
            "Fonte unica, lista separada por virgula, ou 'all'. "
            f"Opcoes: {', '.join(ALL_SOURCE_NAMES)}"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximo de chamadas por fonte. Omita ou use --all para todas as vigentes/abertas.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Coleta todas as chamadas do filtro (sem limite). Padrao recomendado.",
    )
    parser.add_argument(
        "--situacao",
        default="vigente",
        choices=["vigente", "aberta", "todas", "encerrada"],
        help="Filtro FINEP (ignorado nas demais fontes HTML).",
    )
    parser.add_argument(
        "--anexos",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="FINEP: baixa PDFs (edital+anexos); use --no-anexos so para o primario",
    )
    parser.add_argument(
        "--replace-manifest",
        action="store_true",
        help="Reescreve corpus_manifest.csv apenas com o resultado desta coleta",
    )
    parser.add_argument(
        "--finep-only-manifest",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="(legado) Se --source finep, reescreve manifest so com FINEP",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Apos baixar PDFs FINEP, extrai texto em data/texts",
    )
    args = parser.parse_args(argv)

    sources = _parse_sources(args.source)
    limit: int | None = None if args.all or args.limit is None else args.limit
    if args.limit == 0:
        limit = None

    replace = bool(args.replace_manifest)
    if args.finep_only_manifest is True and sources == ["finep"]:
        replace = True
    if args.finep_only_manifest is False:
        replace = False
    # Default legado: coleta so FINEP reescreve o manifest.
    if args.finep_only_manifest is None and sources == ["finep"] and not args.replace_manifest:
        replace = True

    agent = ScraperAgent()
    result = agent.collect(
        sources,
        limit=limit,
        situacao=args.situacao,
        download_anexos=args.anexos,
        replace_manifest=replace,
        extract_texts=bool(args.extract),
    )

    print(f"Fontes: {', '.join(sources)}")
    print(f"Filtro FINEP situacao: {args.situacao}")
    print(f"Limite/fonte: {'nenhum (todas)' if limit is None else limit}")
    print(f"Chamadas: {result.calls}")
    print(f"Alvos (meta): {len(result.targets)}")
    print(f"Arquivos novos: {len(result.downloaded)}")
    print(f"Arquivos em cache/meta: {len(result.cached)}")
    by_source: dict[str, int] = {}
    for t in result.targets:
        src = str(t.get("source") or "?")
        by_source[src] = by_source.get(src, 0) + 1
    if by_source:
        print("Por fonte:")
        for src, n in sorted(by_source.items()):
            print(f"  - {src}: {n}")
    for path in result.downloaded[:15]:
        print(f"  + {path}")
    if len(result.downloaded) > 15:
        print(f"  ... +{len(result.downloaded) - 15} arquivos")
    if result.errors:
        print("Avisos/erros:")
        for err in result.errors[:20]:
            print(f"  ! {err}")

    # Texto de PDFs novos ja e extraido em ScraperAgent quando --extract.
    # Evita reprocessar todo data/raw_pdfs (pode ser centenas de arquivos).

    return 0 if result.ok_count or result.calls else 1


if __name__ == "__main__":
    raise SystemExit(main())
