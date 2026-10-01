"""Extrai texto de PDFs em data/raw_pdfs → data/texts (T-005 / T-013).

Uso (venv ativo, raiz do repo):
  python -m scripts.extract_pdfs
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

from app.config import ROOT_DIR, get_settings

MIN_USEFUL_CHARS = 500


def slugify(name: str) -> str:
    base = Path(name).stem
    base = base.lower()
    base = re.sub(r"[^\w\s-]", "", base, flags=re.UNICODE)
    base = re.sub(r"[-\s]+", "_", base).strip("_")
    return base[:80] or "documento"


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(pdf_path: Path) -> tuple[str, int, int]:
    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    raw = "\n\n".join(parts)
    cleaned = clean_text(raw)
    return cleaned, len(reader.pages), len(cleaned)


def main() -> int:
    settings = get_settings()
    raw_dir = settings.raw_pdfs_dir
    texts_dir = settings.texts_dir
    texts_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(raw_dir.glob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF em {raw_dir}")
        return 1

    print(f"Raiz: {ROOT_DIR}")
    print(f"PDFs: {len(pdfs)} em {raw_dir}\n")

    ok = 0
    weak = 0
    for pdf in pdfs:
        text, pages, n_chars = extract_pdf(pdf)
        out = texts_dir / f"{slugify(pdf.name)}.txt"
        out.write_text(text, encoding="utf-8")
        status = "OK" if n_chars >= MIN_USEFUL_CHARS else "FRACO"
        if n_chars >= MIN_USEFUL_CHARS:
            ok += 1
        else:
            weak += 1
        print(f"[{status}] {pdf.name}")
        print(f"       pages={pages} chars={n_chars} -> {out.relative_to(ROOT_DIR)}")

    print(f"\nResumo: {ok} úteis (>= {MIN_USEFUL_CHARS} chars), {weak} fracos, {len(pdfs)} total")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
