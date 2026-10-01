"""CLI — coleta automatica FINEP (chamadas + anexos + metadados).

Uso:
  python -m scripts.collect_editais --source finep --all --extract
  python -m scripts.collect_editais --source finep --limit 30 --situacao aberta --anexos
"""

from __future__ import annotations

import argparse

from agents.scraper_agent import ScraperAgent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agente Coletor de editais FINEP")
    parser.add_argument("--source", default="finep", choices=["finep"])
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximo de chamadas com PDF. Omita ou use --all para todas as abertas.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Coleta todas as chamadas do filtro (sem limite). Padrao recomendado.",
    )
    parser.add_argument(
        "--situacao",
        default="aberta",
        choices=["aberta", "todas", "encerrada"],
        help="Filtro de situacao na API FINEP",
    )
    parser.add_argument(
        "--anexos",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Baixa todos os PDFs (edital+anexos); use --no-anexos so para o primario",
    )
    parser.add_argument(
        "--finep-only-manifest",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Reescreve corpus_manifest.csv so com FINEP coletada (default: sim)",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Apos baixar, extrai texto dos PDFs em data/texts",
    )
    args = parser.parse_args(argv)

    limit: int | None = None if args.all or args.limit is None else args.limit
    if args.limit == 0:
        limit = None

    agent = ScraperAgent()
    result = agent.collect_finep(
        limit=limit,
        situacao=args.situacao,
        download_anexos=args.anexos,
        finep_only_manifest=args.finep_only_manifest,
        extract_texts=False,
    )

    print(f"Fonte: {result.source}")
    print(f"Filtro situacao: {args.situacao}")
    print(f"Limite: {'nenhum (todas)' if limit is None else limit}")
    print(f"Chamadas: {result.calls}")
    print(f"Alvos (meta): {len(result.targets)}")
    print(f"PDFs baixados agora: {len(result.downloaded)}")
    print(f"PDFs em cache: {len(result.cached)}")
    for path in result.downloaded[:15]:
        print(f"  + {path}")
    if len(result.downloaded) > 15:
        print(f"  ... +{len(result.downloaded) - 15} arquivos")
    if result.errors:
        print("Avisos/erros:")
        for err in result.errors[:20]:
            print(f"  ! {err}")

    if args.extract and result.ok_count:
        from scripts.extract_pdfs import main as extract_main

        print("\n--- Extracao de texto ---")
        code = extract_main()
        if code != 0:
            return code

    return 0 if result.ok_count or result.calls else 1


if __name__ == "__main__":
    raise SystemExit(main())
