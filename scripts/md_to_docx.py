# -*- coding: utf-8 -*-
"""Converte Markdown (CommonMark + tabelas) para .docx via markdown-it-py + python-docx."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from markdown_it import MarkdownIt

NAVY = RGBColor(0x07, 0x0B, 0x2E)
BODY = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x55, 0x55, 0x55)


def set_run_font(run, size=11, bold=False, italic=False, color=None, mono=False):
    font_name = "Consolas" if mono else "Calibri"
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


def add_inline(paragraph, tokens, *, size=11, color=BODY):
    """Renderiza tokens inline (text, strong, em, code_inline, softbreak)."""
    strong = 0
    em = 0
    for tok in tokens:
        if tok.type == "text":
            run = paragraph.add_run(tok.content)
            set_run_font(run, size=size, bold=strong > 0, italic=em > 0, color=color)
        elif tok.type == "code_inline":
            run = paragraph.add_run(tok.content)
            set_run_font(run, size=size - 1 if size > 9 else size, mono=True, color=MUTED)
        elif tok.type == "softbreak":
            paragraph.add_run(" ")
        elif tok.type == "hardbreak":
            paragraph.add_run("\n")
        elif tok.type == "strong_open":
            strong += 1
        elif tok.type == "strong_close":
            strong = max(0, strong - 1)
        elif tok.type == "em_open":
            em += 1
        elif tok.type == "em_close":
            em = max(0, em - 1)
        elif tok.type == "link_open":
            continue
        elif tok.type == "link_close":
            continue
        elif tok.type == "image":
            alt = tok.content or "imagem"
            run = paragraph.add_run(f"[imagem: {alt}]")
            set_run_font(run, size=size, italic=True, color=MUTED)
        else:
            if tok.content:
                run = paragraph.add_run(tok.content)
                set_run_font(run, size=size, bold=strong > 0, italic=em > 0, color=color)


def clean_cell(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("|", " ")).strip()


def convert(md_path: Path, out_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    md = MarkdownIt("commonmark", {"breaks": False}).enable("table")
    tokens = md.parse(text)

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    i = 0
    list_stack: list[str] = []  # "bullet" | "ordered"
    table_rows: list[list[str]] = []
    in_table = False
    current_row: list[str] = []
    in_thead = False

    while i < len(tokens):
        tok = tokens[i]

        if tok.type == "heading_open":
            level = int(tok.tag[1])  # h1 -> 1
            inline = tokens[i + 1]
            h = doc.add_heading("", level=min(level, 3))
            if inline.type == "inline" and inline.children:
                add_inline(h, inline.children, size=16 if level == 1 else (13 if level == 2 else 12), color=NAVY)
            else:
                run = h.add_run(inline.content if inline.type == "inline" else "")
                set_run_font(run, size=16 if level == 1 else 13, bold=True, color=NAVY)
            for run in h.runs:
                set_run_font(run, size=16 if level == 1 else (13 if level == 2 else 12), bold=True, color=NAVY)
            i += 3  # open, inline, close
            continue

        if tok.type == "paragraph_open":
            inline = tokens[i + 1]
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(8)
            if inline.type == "inline":
                if inline.children:
                    add_inline(p, inline.children, size=11, color=BODY)
                else:
                    run = p.add_run(inline.content)
                    set_run_font(run, size=11, color=BODY)
            i += 3
            continue

        if tok.type == "blockquote_open":
            # Collect until blockquote_close; render paragraphs indented/italic
            i += 1
            while i < len(tokens) and tokens[i].type != "blockquote_close":
                if tokens[i].type == "paragraph_open":
                    inline = tokens[i + 1]
                    p = doc.add_paragraph()
                    p.paragraph_format.left_indent = Cm(0.5)
                    p.paragraph_format.space_after = Pt(8)
                    if inline.type == "inline" and inline.children:
                        add_inline(p, inline.children, size=10, color=MUTED)
                        for run in p.runs:
                            run.italic = True
                    elif inline.type == "inline":
                        run = p.add_run(inline.content)
                        set_run_font(run, size=10, italic=True, color=MUTED)
                    i += 3
                else:
                    i += 1
            i += 1  # close
            continue

        if tok.type == "bullet_list_open":
            list_stack.append("bullet")
            i += 1
            continue
        if tok.type == "ordered_list_open":
            list_stack.append("ordered")
            i += 1
            continue
        if tok.type in {"bullet_list_close", "ordered_list_close"}:
            if list_stack:
                list_stack.pop()
            i += 1
            continue

        if tok.type == "list_item_open":
            style = "List Number" if list_stack and list_stack[-1] == "ordered" else "List Bullet"
            # next meaningful content: paragraph_open or inline nested
            i += 1
            # skip paragraph_open if present
            if i < len(tokens) and tokens[i].type == "paragraph_open":
                inline = tokens[i + 1]
                p = doc.add_paragraph(style=style)
                p.paragraph_format.space_after = Pt(3)
                if inline.type == "inline" and inline.children:
                    add_inline(p, inline.children, size=11)
                elif inline.type == "inline":
                    run = p.add_run(inline.content)
                    set_run_font(run, size=11)
                i += 3  # p_open, inline, p_close
            # skip until list_item_close
            while i < len(tokens) and tokens[i].type != "list_item_close":
                # nested lists already handled when we continue outer loop — but we're consuming
                if tokens[i].type in {"bullet_list_open", "ordered_list_open"}:
                    # let outer loop handle by breaking — simpler: flatten nested as bullets
                    nested_style = (
                        "List Number" if tokens[i].type == "ordered_list_open" else "List Bullet"
                    )
                    i += 1
                    while i < len(tokens) and tokens[i].type not in {
                        "bullet_list_close",
                        "ordered_list_close",
                    }:
                        if tokens[i].type == "list_item_open":
                            i += 1
                            if i < len(tokens) and tokens[i].type == "paragraph_open":
                                inline = tokens[i + 1]
                                p = doc.add_paragraph(style=nested_style)
                                p.paragraph_format.space_after = Pt(2)
                                if inline.type == "inline" and inline.children:
                                    add_inline(p, inline.children, size=10)
                                i += 3
                            while i < len(tokens) and tokens[i].type != "list_item_close":
                                i += 1
                            i += 1
                        else:
                            i += 1
                    i += 1
                else:
                    i += 1
            i += 1  # list_item_close
            continue

        if tok.type == "fence" or tok.type == "code_block":
            lang = (tok.info or "").strip()
            code = tok.content.rstrip("\n")
            if lang:
                cap = doc.add_paragraph()
                cap.paragraph_format.space_after = Pt(2)
                run = cap.add_run(f"[{lang}]")
                set_run_font(run, size=9, italic=True, color=MUTED)
            for line in code.splitlines() or [""]:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.left_indent = Cm(0.3)
                run = p.add_run(line if line else " ")
                set_run_font(run, size=9, mono=True, color=BODY)
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(8)
            i += 1
            continue

        if tok.type == "hr":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run("—" * 24)
            set_run_font(run, size=10, color=MUTED)
            i += 1
            continue

        if tok.type == "table_open":
            in_table = True
            table_rows = []
            current_row = []
            i += 1
            continue

        if tok.type == "thead_open":
            in_thead = True
            i += 1
            continue
        if tok.type == "thead_close":
            in_thead = False
            i += 1
            continue
        if tok.type == "tbody_open" or tok.type == "tbody_close":
            i += 1
            continue

        if tok.type == "tr_open":
            current_row = []
            i += 1
            continue

        if tok.type == "tr_close":
            if current_row:
                table_rows.append(current_row)
            current_row = []
            i += 1
            continue

        if tok.type in {"th_open", "td_open"}:
            inline = tokens[i + 1]
            cell_text = ""
            if inline.type == "inline":
                cell_text = inline.content
                if inline.children:
                    parts = []
                    for c in inline.children:
                        if c.type in {"text", "code_inline"}:
                            parts.append(c.content)
                        elif c.type == "softbreak":
                            parts.append(" ")
                    if parts:
                        cell_text = "".join(parts)
            current_row.append(clean_cell(cell_text))
            # skip open, inline, close
            i += 3
            continue

        if tok.type == "table_close":
            if table_rows:
                cols = max(len(r) for r in table_rows)
                table = doc.add_table(rows=len(table_rows), cols=cols)
                table.style = "Table Grid"
                for r_idx, row in enumerate(table_rows):
                    for c_idx in range(cols):
                        cell = table.cell(r_idx, c_idx)
                        cell.text = ""
                        p = cell.paragraphs[0]
                        val = row[c_idx] if c_idx < len(row) else ""
                        run = p.add_run(val)
                        set_run_font(
                            run,
                            size=9,
                            bold=(r_idx == 0),
                            color=NAVY if r_idx == 0 else BODY,
                        )
                doc.add_paragraph().paragraph_format.space_after = Pt(10)
            in_table = False
            table_rows = []
            i += 1
            continue

        # ignore closers / unknowns
        i += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Markdown → Word (.docx)")
    parser.add_argument(
        "input",
        nargs="?",
        default=str(root / "docs" / "TCC" / "DOCUMENTACAO_TECNICA_DESENVOLVIMENTO.md"),
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Caminho do .docx de saída",
    )
    args = parser.parse_args()
    md_path = Path(args.input).resolve()
    out_path = (
        Path(args.output).resolve()
        if args.output
        else md_path.with_suffix(".docx")
    )
    convert(md_path, out_path)
    print(f"Gerado: {out_path}")


if __name__ == "__main__":
    main()
