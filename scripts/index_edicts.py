"""CLI — indexa edicts no pgvector (T-020).

Uso:
  python -m scripts.index_edicts
  python -m scripts.index_edicts --reindex
  python -m scripts.index_edicts --smoke "startup inovacao digital"
"""

from __future__ import annotations

import argparse
import asyncio

from agents.indexer_agent import IndexerAgent


async def _run(args: argparse.Namespace) -> int:
    agent = IndexerAgent()
    result = await agent.index_edicts(only_missing=not args.reindex, limit=args.limit)
    print(
        f"\nIndexados={result.ok_count} erros={len(result.errors)} "
        f"skipped={len(result.skipped)}"
    )
    if result.errors:
        return 1

    if args.smoke:
        print(f"\nSmoke similarity: {args.smoke!r}")
        hits = await agent.smoke_similarity(args.smoke, k=args.k)
        for i, hit in enumerate(hits, 1):
            print(
                f"  {i}. {hit.get('external_id')} | dist={float(hit['distance']):.4f} | "
                f"{(hit.get('title') or '')[:70]}"
            )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Indexador de editais (pgvector)")
    parser.add_argument("--reindex", action="store_true", help="Regrava embeddings existentes")
    parser.add_argument("--limit", type=int, default=None, help="Limite de registros")
    parser.add_argument("--smoke", type=str, default=None, help="Query de smoke test")
    parser.add_argument("--k", type=int, default=5, help="Top-k do smoke test")
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
