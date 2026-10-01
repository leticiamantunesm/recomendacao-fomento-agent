"""Pipeline: coleta FINEP fresca → extract → seed FINEP-only → reindex.

Uso:
  python -m scripts.refresh_finep_corpus --all
  python -m scripts.refresh_finep_corpus --limit 20
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
    parser = argparse.ArgumentParser(description="Refresh corpus FINEP para a UI")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximo de chamadas. Omita ou use --all para todas as abertas.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Coleta todas as chamadas do filtro (default).",
    )
    parser.add_argument("--no-all", action="store_true", help="Desativa --all e usa --limit")
    parser.add_argument("--situacao", default="aberta", choices=["aberta", "todas", "encerrada"])
    parser.add_argument("--no-anexos", action="store_true")
    args = parser.parse_args()

    use_all = args.all and not args.no_all and args.limit is None
    py = sys.executable
    collect_cmd = [
        py,
        "-m",
        "scripts.collect_editais",
        "--source",
        "finep",
        "--situacao",
        args.situacao,
        "--extract",
        "--finep-only-manifest",
        *(["--no-anexos"] if args.no_anexos else ["--anexos"]),
    ]
    if use_all or args.limit is None or args.limit == 0:
        collect_cmd.append("--all")
    else:
        collect_cmd.extend(["--limit", str(args.limit)])

    code = _run(collect_cmd)
    if code != 0:
        return code

    code = _run([py, "-m", "scripts.seed_corpus", "--agency", "FINEP", "--purge-other"])
    if code != 0:
        return code

    code = _run([py, "-m", "scripts.index_edicts", "--reindex"])
    if code != 0:
        return code

    print("\nrefresh_finep_corpus: OK — UI passa a ranquear so FINEP fresca.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
