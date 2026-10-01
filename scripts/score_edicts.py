"""CLI — Scoring Agent (T-040).

Uso:
  python -m scripts.score_edicts --query "startup inovacao digital" --agency FINEP
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from agents.retrieval_agent import CompanyProfile, ProjectQuery
from agents.scoring_agent import ScoringAgent
from app.config import ROOT_DIR


async def _run(args: argparse.Namespace) -> int:
    project = ProjectQuery(title=args.title or "Consulta avulsa", text=args.query)
    areas = [a.strip() for a in (args.areas or "").split(";") if a.strip()]
    company = CompanyProfile(
        name=args.company,
        size=args.size,
        trl=args.trl,
        areas=areas,
    )
    agent = ScoringAgent()
    result = await agent.score_from_retrieval(
        project,
        company,
        k=args.k,
        agency=args.agency,
    )

    print(f"Projeto: {result.project_title}")
    print(f"Empresa: {result.company_name}")
    print()
    for i, r in enumerate(result.reports, 1):
        print(f"{i}. SCORE {r.score:.1f}/100 | elegivel={r.eligible} | {r.external_id} — {r.title}")
        print(
            f"   breakdown: sim={r.breakdown.similarity} area={r.breakdown.area} "
            f"trl={r.breakdown.trl} size={r.breakdown.size} "
            f"region={r.breakdown.region} budget={r.breakdown.budget}"
        )
        print(f"   resumo: {r.summary}")
        if r.strengths:
            print("   forcas:")
            for s in r.strengths:
                print(f"     + {s}")
        if r.weaknesses:
            print("   fraquezas:")
            for w in r.weaknesses:
                print(f"     - {w}")
        print()

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT_DIR / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON salvo em {out}")
    return 0 if result.reports else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Scoring Agent (0-100 + feedback)")
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--title", type=str, default=None)
    parser.add_argument("--company", type=str, default="Empresa Demo TCC")
    parser.add_argument("--size", type=str, default="EPP")
    parser.add_argument("--trl", type=int, default=5)
    parser.add_argument("--areas", type=str, default="inovacao;tecnologias digitais")
    parser.add_argument("--agency", type=str, default=None)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--out", type=str, default="data/outputs/scoring_last.json")
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
