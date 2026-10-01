"""CLI — pipeline E2E (T-042).

Uso:
  python -m scripts.run_pipeline --query "startup inovacao digital IA"
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from agents.orchestrator import Orchestrator, PipelineRequest
from app.config import ROOT_DIR
from db.session import dispose_engine


async def _run(args: argparse.Namespace) -> int:
    areas = [a.strip() for a in (args.areas or "").split(";") if a.strip()]
    orch = Orchestrator()
    result = await orch.run(
        PipelineRequest(
            project_title=args.title or "Consulta avulsa",
            project_text=args.query,
            company_name=args.company,
            company_size=args.size,
            company_trl=args.trl,
            company_areas=areas,
            agency=args.agency,
            k=args.k,
            top_n_drafts=args.drafts,
        )
    )
    await dispose_engine()

    print(f"created_at: {result.created_at}")
    print(f"report: {result.report_path}")
    print(f"matches: {len((result.retrieval or {}).get('matches') or [])}")
    print(f"drafts: {len(result.drafts)}")
    if result.drafts:
        d0 = result.drafts[0]
        print(f"top draft: {d0.get('external_id')} score={d0.get('score')} chars={len(d0.get('text') or '')}")

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT_DIR / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON: {out}")
    return 0 if result.drafts else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Orquestrador E2E do TCC")
    parser.add_argument("--query", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--company", default="Empresa Demo TCC")
    parser.add_argument("--size", default="EPP")
    parser.add_argument("--trl", type=int, default=5)
    parser.add_argument("--areas", default="inovacao;tecnologias digitais")
    parser.add_argument("--agency", default="FINEP")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--drafts", type=int, default=1)
    parser.add_argument("--out", default="data/outputs/pipeline_last.json")
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
