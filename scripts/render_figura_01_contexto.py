"""Gera Figura 1 — diagrama de contexto SADS (PNG + SVG)."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "TCC" / "figuras"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"]
        if bold
        else ["segoeui.ttf", "arial.ttf", "calibri.ttf"]
    )
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    w, h = 1400, 920
    img = Image.new("RGB", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    f_title = load_font(26, True)
    f_box = load_font(17, True)
    f_sub = load_font(13, False)
    f_cap = load_font(13, False)
    f_group = load_font(14, True)

    navy, cyan, muted = "#070b2e", "#1490d4", "#5a6a85"
    soft, border, actor = "#eef2f8", "#c5d0e0", "#e8f6fc"

    def text_size(text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
        b = draw.textbbox((0, 0), text, font=font)
        return b[2] - b[0], b[3] - b[1]

    def center_text(x: int, y: int, box_w: int, text: str, font: ImageFont.ImageFont, fill: str) -> None:
        tw, _ = text_size(text, font)
        draw.text((x + (box_w - tw) / 2, y), text, fill=fill, font=font)

    def group(x: int, y: int, gw: int, gh: int, label: str) -> None:
        draw.rounded_rectangle((x, y, x + gw, y + gh), radius=16, fill=soft, outline=border, width=1)
        draw.text((x + 16, y + 10), label, fill=muted, font=f_group)

    def box(
        x: int,
        y: int,
        bw: int,
        bh: int,
        title: str,
        subtitle: str,
        fill: str = "#FFFFFF",
        outline: str = border,
        title_fill: str = navy,
    ) -> None:
        draw.rounded_rectangle((x, y, x + bw, y + bh), radius=12, fill=fill, outline=outline, width=2)
        center_text(x, y + 18, bw, title, f_box, title_fill)
        if subtitle:
            for i, line in enumerate(subtitle.split("|")):
                center_text(x, y + 46 + i * 18, bw, line.strip(), f_sub, muted)

    def arrow(x1: float, y1: float, x2: float, y2: float, label: str | None = None) -> None:
        draw.line((x1, y1, x2, y2), fill=cyan, width=3)
        ang = math.atan2(y2 - y1, x2 - x1)
        s = 11
        p1 = (x2 - s * math.cos(ang - 0.45), y2 - s * math.sin(ang - 0.45))
        p2 = (x2 - s * math.cos(ang + 0.45), y2 - s * math.sin(ang + 0.45))
        draw.polygon([(x2, y2), p1, p2], fill=cyan)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            tw, th = text_size(label, f_cap)
            draw.rectangle((mx - tw / 2 - 5, my - th / 2 - 3, mx + tw / 2 + 5, my + th / 2 + 3), fill="#FFFFFF")
            draw.text((mx - tw / 2, my - th / 2), label, fill=muted, font=f_cap)

    title = "Figura 1 — Diagrama de contexto do SADS"
    tw, _ = text_size(title, f_title)
    draw.text(((w - tw) / 2, 22), title, fill=navy, font=f_title)

    group(40, 90, 280, 340, "Clientes")
    group(360, 90, 520, 560, "Aplicação SADS")
    group(920, 90, 440, 270, "Dados")
    group(920, 390, 440, 260, "Sistemas externos")

    box(70, 150, 220, 95, "Visitante", "público / landing", actor, cyan)
    box(70, 290, 220, 95, "Usuário autenticado", "empresa / analista", actor, cyan)

    box(400, 150, 200, 95, "Landing", "Next.js estático", outline=cyan)
    box(640, 150, 200, 95, "UI web", "HTML / JS Fase A", outline=cyan)
    draw.rounded_rectangle((480, 310, 760, 415), radius=12, fill=navy, outline=navy, width=2)
    center_text(480, 328, 280, "API FastAPI", f_box, "#FFFFFF")
    center_text(480, 358, 280, "auth, projetos, evaluate", f_sub, "#cfefff")

    box(480, 470, 280, 120, "Agentes", "coleta, indexação|retrieval, scoring", soft, cyan)

    box(960, 150, 360, 95, "Neon PostgreSQL", "+ pgvector (editais, projetos)", outline=cyan)
    box(960, 270, 360, 70, "Armazenamento local", "PDFs / artefatos", soft, border)

    box(960, 450, 360, 75, "API FINEP", "corpus de editais (piloto)", "#f7fafc", border)
    box(960, 545, 360, 75, "BrasilAPI", "consulta CNPJ", "#f7fafc", border)

    arrow(290, 197, 400, 197)
    arrow(290, 337, 640, 230)
    arrow(500, 245, 580, 310)
    arrow(740, 245, 680, 310)
    arrow(760, 350, 960, 197, "CRUD / vetores")
    arrow(620, 415, 620, 470)
    arrow(760, 530, 960, 305)
    arrow(760, 545, 960, 487, "coleta")
    arrow(760, 380, 960, 582, "CNPJ")

    cap = "Fonte: Elaboração própria (2026), a partir da arquitetura do SADS."
    cw, _ = text_size(cap, f_cap)
    draw.text(((w - cw) / 2, h - 36), cap, fill=muted, font=f_cap)

    png = OUT_DIR / "figura_01_contexto_sads.png"
    img.save(png, "PNG")
    print(f"Wrote {png} ({png.stat().st_size} bytes)")

    # SVG companion (editável / Word)
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="920" viewBox="0 0 1400 920">
  <rect width="1400" height="920" fill="#fff"/>
  <text x="700" y="42" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="26" font-weight="700" fill="#070b2e">Figura 1 — Diagrama de contexto do SADS</text>
  <image href="figura_01_contexto_sads.png" x="0" y="0" width="1400" height="920"/>
</svg>
"""
    # Prefer standalone SVG without embedding raster dependency for Word - rewrite pure SVG
    svg_path = OUT_DIR / "figura_01_contexto_sads.svg"
    svg_path.write_text(_pure_svg(), encoding="utf-8")
    print(f"Wrote {svg_path}")


def _pure_svg() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="920" viewBox="0 0 1400 920" font-family="Segoe UI, Arial, sans-serif">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#1490d4"/>
    </marker>
  </defs>
  <rect width="1400" height="920" fill="#ffffff"/>
  <text x="700" y="42" text-anchor="middle" font-size="26" font-weight="700" fill="#070b2e">Figura 1 — Diagrama de contexto do SADS</text>

  <!-- groups -->
  <rect x="40" y="90" width="280" height="340" rx="16" fill="#eef2f8" stroke="#c5d0e0"/>
  <text x="56" y="114" font-size="14" font-weight="700" fill="#5a6a85">Clientes</text>
  <rect x="360" y="90" width="520" height="560" rx="16" fill="#eef2f8" stroke="#c5d0e0"/>
  <text x="376" y="114" font-size="14" font-weight="700" fill="#5a6a85">Aplicação SADS</text>
  <rect x="920" y="90" width="440" height="270" rx="16" fill="#eef2f8" stroke="#c5d0e0"/>
  <text x="936" y="114" font-size="14" font-weight="700" fill="#5a6a85">Dados</text>
  <rect x="920" y="390" width="440" height="260" rx="16" fill="#eef2f8" stroke="#c5d0e0"/>
  <text x="936" y="414" font-size="14" font-weight="700" fill="#5a6a85">Sistemas externos</text>

  <!-- boxes -->
  <g>
    <rect x="70" y="150" width="220" height="95" rx="12" fill="#e8f6fc" stroke="#1490d4" stroke-width="2"/>
    <text x="180" y="188" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">Visitante</text>
    <text x="180" y="214" text-anchor="middle" font-size="13" fill="#5a6a85">público / landing</text>
  </g>
  <g>
    <rect x="70" y="290" width="220" height="95" rx="12" fill="#e8f6fc" stroke="#1490d4" stroke-width="2"/>
    <text x="180" y="328" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">Usuário autenticado</text>
    <text x="180" y="354" text-anchor="middle" font-size="13" fill="#5a6a85">empresa / analista</text>
  </g>
  <g>
    <rect x="400" y="150" width="200" height="95" rx="12" fill="#fff" stroke="#1490d4" stroke-width="2"/>
    <text x="500" y="188" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">Landing</text>
    <text x="500" y="214" text-anchor="middle" font-size="13" fill="#5a6a85">Next.js estático</text>
  </g>
  <g>
    <rect x="640" y="150" width="200" height="95" rx="12" fill="#fff" stroke="#1490d4" stroke-width="2"/>
    <text x="740" y="188" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">UI web</text>
    <text x="740" y="214" text-anchor="middle" font-size="13" fill="#5a6a85">HTML / JS Fase A</text>
  </g>
  <g>
    <rect x="480" y="310" width="280" height="105" rx="12" fill="#070b2e" stroke="#070b2e" stroke-width="2"/>
    <text x="620" y="352" text-anchor="middle" font-size="17" font-weight="700" fill="#ffffff">API FastAPI</text>
    <text x="620" y="380" text-anchor="middle" font-size="13" fill="#cfefff">auth, projetos, evaluate</text>
  </g>
  <g>
    <rect x="480" y="470" width="280" height="120" rx="12" fill="#eef2f8" stroke="#1490d4" stroke-width="2"/>
    <text x="620" y="512" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">Agentes</text>
    <text x="620" y="538" text-anchor="middle" font-size="13" fill="#5a6a85">coleta, indexação</text>
    <text x="620" y="558" text-anchor="middle" font-size="13" fill="#5a6a85">retrieval, scoring</text>
  </g>
  <g>
    <rect x="960" y="150" width="360" height="95" rx="12" fill="#fff" stroke="#1490d4" stroke-width="2"/>
    <text x="1140" y="188" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">Neon PostgreSQL</text>
    <text x="1140" y="214" text-anchor="middle" font-size="13" fill="#5a6a85">+ pgvector (editais, projetos)</text>
  </g>
  <g>
    <rect x="960" y="270" width="360" height="70" rx="12" fill="#eef2f8" stroke="#c5d0e0" stroke-width="2"/>
    <text x="1140" y="300" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">Armazenamento local</text>
    <text x="1140" y="322" text-anchor="middle" font-size="13" fill="#5a6a85">PDFs / artefatos</text>
  </g>
  <g>
    <rect x="960" y="450" width="360" height="75" rx="12" fill="#f7fafc" stroke="#c5d0e0" stroke-width="2"/>
    <text x="1140" y="482" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">API FINEP</text>
    <text x="1140" y="506" text-anchor="middle" font-size="13" fill="#5a6a85">corpus de editais (piloto)</text>
  </g>
  <g>
    <rect x="960" y="545" width="360" height="75" rx="12" fill="#f7fafc" stroke="#c5d0e0" stroke-width="2"/>
    <text x="1140" y="577" text-anchor="middle" font-size="17" font-weight="700" fill="#070b2e">BrasilAPI</text>
    <text x="1140" y="601" text-anchor="middle" font-size="13" fill="#5a6a85">consulta CNPJ</text>
  </g>

  <!-- arrows -->
  <line x1="290" y1="197" x2="400" y2="197" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="290" y1="337" x2="640" y2="230" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="500" y1="245" x2="580" y2="310" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="740" y1="245" x2="680" y2="310" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="760" y1="350" x2="960" y2="197" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <text x="860" y="255" text-anchor="middle" font-size="12" fill="#5a6a85">CRUD / vetores</text>
  <line x1="620" y1="415" x2="620" y2="470" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="760" y1="530" x2="960" y2="305" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="760" y1="545" x2="960" y2="487" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <text x="855" y="528" text-anchor="middle" font-size="12" fill="#5a6a85">coleta</text>
  <line x1="760" y1="380" x2="960" y2="582" stroke="#1490d4" stroke-width="3" marker-end="url(#arrow)"/>
  <text x="900" y="520" text-anchor="middle" font-size="12" fill="#5a6a85">CNPJ</text>

  <text x="700" y="890" text-anchor="middle" font-size="13" fill="#5a6a85">Fonte: Elaboração própria (2026), a partir da arquitetura do SADS.</text>
</svg>
"""


if __name__ == "__main__":
    main()
