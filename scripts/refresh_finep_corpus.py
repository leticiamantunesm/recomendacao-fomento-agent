"""Pipeline: coleta de fontes → extract (FINEP) → seed → reindex.

Uso:
  python -m scripts.refresh_finep_corpus --all
  python -m scripts.refresh_finep_corpus --source all --all
  python -m scripts.refresh_finep_corpus --source finep,fapesp,cnpq --limit 20
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from app.config import ROOT_DIR


def _run(cmd: list[str]) -> int:
    print("\n>>", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT_DIR))


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh corpus de editais para a UI")
    parser.add_argument(
        "--source",
        default="finep",
        help="Fonte unica, lista (finep,fapesp,...) ou 'all'. Default: finep.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximo de chamadas por fonte. Omita ou use --all para todas as vigentes.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Coleta todas as chamadas do filtro (default).",
    )
    parser.add_argument("--no-all", action="store_true", help="Desativa --all e usa --limit")
    parser.add_argument(
        "--situacao",
        default="vigente",
        choices=["vigente", "aberta", "todas", "encerrada"],
        help="Padrao vigente (Aberta + prazo/vigencia validos) — FINEP.",
    )
    parser.add_argument("--no-anexos", action="store_true")
    args = parser.parse_args()

    use_all = args.all and not args.no_all and args.limit is None
    py = sys.executable
    sources = (args.source or "finep").strip().lower()
    source_parts = (
        ["finep", "fapesp", "cnpq", "centelha", "embrapii", "bndes"]
        if sources in {"all", "*"}
        else [p.strip() for p in sources.split(",") if p.strip()]
    )
    # Extrai PDFs quando FINEP / FAPESP / Embrapii / BNDES entram na coleta.
    want_extract = sources in {"all", "*"} or any(
        s in {"finep", "fapesp", "embrapii", "bndes"} for s in source_parts
    )
    # replace-manifest so quando FINEP entra (ou 'all'): rebuild coerente.
    # Sem FINEP, faz upsert para nao apagar linhas FINEP do manifest.
    replace_manifest = sources in {"all", "*"} or "finep" in source_parts
    collect_cmd = [
        py,
        "-m",
        "scripts.collect_editais",
        "--source",
        sources,
        "--situacao",
        args.situacao,
        *(["--replace-manifest"] if replace_manifest else []),
        *(["--extract"] if want_extract else []),
        *(["--no-anexos"] if args.no_anexos else ["--anexos"]),
    ]
    if use_all or args.limit is None or args.limit == 0:
        collect_cmd.append("--all")
    else:
        collect_cmd.extend(["--limit", str(args.limit)])

    code = _run(collect_cmd)
    if code != 0:
        return code

    # Purge so de nao-FINEP quando a coleta e exclusivamente FINEP (piloto legado).
    seed_cmd = [py, "-m", "scripts.seed_corpus"]
    if source_parts == ["finep"]:
        seed_cmd.extend(["--agency", "FINEP", "--purge-other"])
    code = _run(seed_cmd)
    if code != 0:
        return code

    code = _run([py, "-m", "scripts.index_edicts", "--reindex"])
    if code != 0:
        return code

    print(f"\nrefresh_finep_corpus: OK — fontes={sources}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
