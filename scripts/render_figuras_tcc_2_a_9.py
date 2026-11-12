"""Gera Figuras 2–9 do TCC (diagramas + screenshots legendados)."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "TCC" / "figuras"
FOTOS = ROOT / "docs" / "fotos"

NAVY, CYAN, MUTED = "#070b2e", "#1490d4", "#5a6a85"
SOFT, BORDER, ACTOR = "#eef2f8", "#c5d0e0", "#e8f6fc"
ACCENT = "#0d6e8f"


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


class Canvas:
    def __init__(self, w: int, h: int, title: str, caption: str) -> None:
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w, h), "#FFFFFF")
        self.draw = ImageDraw.Draw(self.img)
        self.f_title = load_font(24, True)
        self.f_box = load_font(16, True)
        self.f_sub = load_font(12, False)
        self.f_cap = load_font(12, False)
        self.f_group = load_font(13, True)
        self.f_tiny = load_font(11, False)
        self.caption = caption
        tw, _ = self.text_size(title, self.f_title)
        self.draw.text(((w - tw) / 2, 18), title, fill=NAVY, font=self.f_title)
        cw, _ = self.text_size(caption, self.f_cap)
        self.draw.text(((w - cw) / 2, h - 32), caption, fill=MUTED, font=self.f_cap)

    def text_size(self, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
        b = self.draw.textbbox((0, 0), text, font=font)
        return b[2] - b[0], b[3] - b[1]

    def center_text(self, x: int, y: int, box_w: int, text: str, font: ImageFont.ImageFont, fill: str) -> None:
        tw, _ = self.text_size(text, font)
        self.draw.text((x + (box_w - tw) / 2, y), text, fill=fill, font=font)

    def group(self, x: int, y: int, gw: int, gh: int, label: str) -> None:
        self.draw.rounded_rectangle((x, y, x + gw, y + gh), radius=14, fill=SOFT, outline=BORDER, width=1)
        self.draw.text((x + 14, y + 8), label, fill=MUTED, font=self.f_group)

    def box(
        self,
        x: int,
        y: int,
        bw: int,
        bh: int,
        title: str,
        subtitle: str = "",
        fill: str = "#FFFFFF",
        outline: str = BORDER,
        title_fill: str = NAVY,
        dark: bool = False,
    ) -> tuple[int, int, int, int]:
        if dark:
            fill, outline, title_fill = NAVY, NAVY, "#FFFFFF"
        self.draw.rounded_rectangle((x, y, x + bw, y + bh), radius=12, fill=fill, outline=outline, width=2)
        lines = [ln.strip() for ln in title.split("|") if ln.strip()]
        start_y = y + (14 if len(lines) == 1 and not subtitle else 12)
        for i, line in enumerate(lines):
            self.center_text(x, start_y + i * 18, bw, line, self.f_box, title_fill)
        if subtitle:
            base = start_y + len(lines) * 18 + 4
            for i, line in enumerate(subtitle.split("|")):
                color = "#cfefff" if dark else MUTED
                self.center_text(x, base + i * 16, bw, line.strip(), self.f_sub, color)
        return x, y, x + bw, y + bh

    def arrow(self, x1: float, y1: float, x2: float, y2: float, label: str | None = None) -> None:
        self.draw.line((x1, y1, x2, y2), fill=CYAN, width=3)
        ang = math.atan2(y2 - y1, x2 - x1)
        s = 11
        p1 = (x2 - s * math.cos(ang - 0.45), y2 - s * math.sin(ang - 0.45))
        p2 = (x2 - s * math.cos(ang + 0.45), y2 - s * math.sin(ang + 0.45))
        self.draw.polygon([(x2, y2), p1, p2], fill=CYAN)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            tw, th = self.text_size(label, self.f_tiny)
            self.draw.rectangle(
                (mx - tw / 2 - 4, my - th / 2 - 2, mx + tw / 2 + 4, my + th / 2 + 2),
                fill="#FFFFFF",
            )
            self.draw.text((mx - tw / 2, my - th / 2), label, fill=MUTED, font=self.f_tiny)

    def save(self, stem: str) -> Path:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        png = OUT_DIR / f"{stem}.png"
        self.img.save(png, "PNG")
        print(f"Wrote {png} ({png.stat().st_size} bytes)")
        return png


def figura_02() -> None:
    c = Canvas(
        1500,
        720,
        "Figura 2 — Fluxo de recomendação (evaluate)",
        "Fonte: Elaboração própria (2026).",
    )
    # Entrada
    c.group(40, 80, 280, 520, "Entrada")
    c.box(70, 140, 220, 100, "projects.raw_text", "texto do PDF / formulário", ACTOR, CYAN)
    c.box(70, 280, 220, 100, "company", "porte, UF, áreas, CNPJ", ACTOR, CYAN)
    c.box(70, 420, 220, 100, "project form", "TRL, orçamento, temas", SOFT, BORDER)

    # Pipeline
    c.group(360, 80, 780, 520, "Pipeline de avaliação")
    c.box(400, 160, 180, 110, "Retrieval", "filtros + similaridade|vetorial", outline=CYAN)
    c.box(640, 160, 180, 110, "EdictMatch", "candidatos do corpus", outline=CYAN)
    c.box(880, 160, 200, 110, "Scoring", "pesos + hard gates|Gate 0 / risco", dark=True)
    c.box(520, 380, 420, 140, "applications", "score, critérios,|fortes/fracos, orientação", SOFT, CYAN)

    # Saída
    c.group(1180, 80, 280, 520, "Saída")
    c.box(1210, 220, 220, 140, "project-evaluate", "relatório na UI|ranking + alertas", ACTOR, CYAN)

    c.arrow(290, 190, 400, 210)
    c.arrow(290, 330, 400, 230)
    c.arrow(290, 470, 490, 270)
    c.arrow(580, 215, 640, 215)
    c.arrow(820, 215, 880, 215)
    c.arrow(980, 270, 730, 380)
    c.arrow(940, 450, 1210, 290, "persiste / exibe")
    c.save("figura_02_fluxo_recomendacao")


def figura_03() -> None:
    c = Canvas(
        1500,
        820,
        "Figura 3 — Pipeline de agentes de software",
        "Fonte: Elaboração própria (2026).",
    )
    c.group(40, 80, 1420, 200, "Ingestão do corpus (operação)")
    c.box(80, 130, 220, 100, "Scraper", "FINEP (piloto)", outline=CYAN)
    c.box(380, 130, 220, 100, "Indexer", "embeddings +|pgvector", outline=CYAN)
    c.box(680, 130, 280, 100, "Edicts (DB)", "metadados + vetores", SOFT, BORDER)
    c.arrow(300, 180, 380, 180, "editais")
    c.arrow(600, 180, 680, 180, "indexa")

    c.group(40, 320, 1420, 420, "Avaliação de projeto (runtime)")
    c.box(80, 380, 220, 110, "FormExtraction", "PDF → campos|revisão humana", ACTOR, CYAN)
    c.box(360, 380, 200, 110, "Gate0", "project_risk|P&D vs crédito", dark=True)
    c.box(620, 380, 200, 110, "Retrieval", "candidatos", outline=CYAN)
    c.box(880, 380, 200, 110, "Scoring", "matriz + gates", outline=CYAN)
    c.box(1140, 380, 240, 110, "Generation", "templates|sem LLM (padrão)", outline=CYAN)

    c.box(360, 560, 520, 120, "project_risk", "sinais de risco tecnológico / modernização|orienta preferência de instrumento", SOFT, CYAN)
    c.box(920, 560, 460, 120, "Relatório", "applications + textos explicativos|project-evaluate.html", ACTOR, CYAN)

    c.arrow(300, 435, 360, 435)
    c.arrow(560, 435, 620, 435)
    c.arrow(820, 435, 880, 435)
    c.arrow(1080, 435, 1140, 435)
    c.arrow(460, 490, 520, 560)
    c.arrow(980, 490, 1050, 560)
    c.arrow(820, 230, 720, 380, "corpus")
    c.save("figura_03_pipeline_agentes")


def figura_04() -> None:
    c = Canvas(
        1400,
        900,
        "Figura 4 — Modelo entidade-relacionamento (simplificado)",
        "Fonte: Elaboração própria (2026).",
    )

    def entity(x: int, y: int, bw: int, bh: int, name: str, fields: str) -> None:
        c.draw.rounded_rectangle((x, y, x + bw, y + bh), radius=10, fill="#FFFFFF", outline=CYAN, width=2)
        c.draw.rectangle((x, y, x + bw, y + 36), fill=NAVY)
        # top rounded look
        c.draw.rounded_rectangle((x, y, x + bw, y + 36), radius=10, fill=NAVY)
        c.draw.rectangle((x, y + 18, x + bw, y + 36), fill=NAVY)
        c.center_text(x, y + 8, bw, name, c.f_box, "#FFFFFF")
        for i, line in enumerate(fields.split("|")):
            c.draw.text((x + 14, y + 48 + i * 20), line.strip(), fill=MUTED, font=c.f_sub)

    entity(80, 120, 280, 200, "Company", "id|name, cnpj, porte|uf, áreas…")
    entity(80, 400, 280, 180, "Employee", "id, company_id|email, role|password_hash…")
    entity(480, 120, 280, 220, "Project", "id, company_id|title, raw_text|form JSON, status…")
    entity(480, 420, 280, 180, "Document", "id, company_id|project_id?|arquivo, tipo…")
    entity(880, 120, 320, 220, "Edict", "id, source, title|metadata|embedding[384]…")
    entity(780, 420, 360, 220, "Application", "id, project_id, edict_id|score, details|strengths/weaknesses…")

    # Company 1–N Employee
    c.arrow(220, 320, 220, 400)
    c.draw.text((228, 350), "1", fill=ACCENT, font=c.f_tiny)
    c.draw.text((228, 380), "N", fill=ACCENT, font=c.f_tiny)
    # Company 1–N Project
    c.arrow(360, 200, 480, 200)
    c.draw.text((400, 180), "1", fill=ACCENT, font=c.f_tiny)
    c.draw.text((450, 180), "N", fill=ACCENT, font=c.f_tiny)
    # Company 1–N Document
    c.arrow(220, 320, 480, 480)
    c.draw.text((280, 380), "1", fill=ACCENT, font=c.f_tiny)
    c.draw.text((450, 470), "N", fill=ACCENT, font=c.f_tiny)
    # Company 1–N Application
    c.arrow(360, 280, 780, 500)
    c.draw.text((480, 360), "1", fill=ACCENT, font=c.f_tiny)
    c.draw.text((740, 490), "N", fill=ACCENT, font=c.f_tiny)
    # Project 1–N Application
    c.arrow(620, 340, 850, 420)
    c.draw.text((640, 360), "1", fill=ACCENT, font=c.f_tiny)
    c.draw.text((820, 400), "N", fill=ACCENT, font=c.f_tiny)
    # Edict 1–N Application
    c.arrow(1040, 340, 960, 420)
    c.draw.text((1045, 360), "1", fill=ACCENT, font=c.f_tiny)
    c.draw.text((970, 400), "N", fill=ACCENT, font=c.f_tiny)

    c.draw.text(
        (80, 760),
        "Relações: Company 1–N Employee / Project / Document / Application; Edict 1–N Application; Project 1–N Application.",
        fill=MUTED,
        font=c.f_tiny,
    )
    c.save("figura_04_er_simplificado")


def figura_05() -> None:
    c = Canvas(
        1400,
        780,
        "Figura 5 — Fluxo de autenticação e acesso à API",
        "Fonte: Elaboração própria (2026).",
    )
    c.group(40, 90, 300, 560, "Cliente (UI)")
    c.box(70, 160, 240, 100, "register / login", "credenciais do usuário", ACTOR, CYAN)
    c.box(70, 340, 240, 100, "Token Bearer", "armazenado na sessão", SOFT, CYAN)
    c.box(70, 500, 240, 100, "Chamadas API", "Authorization: Bearer …", outline=CYAN)

    c.group(400, 90, 520, 560, "API FastAPI")
    c.box(460, 160, 400, 110, "POST /auth/register|/auth/login", "PBKDF2-SHA256 + HMAC", dark=True)
    c.box(460, 340, 400, 110, "Validação do token", "assinatura + expiração", outline=CYAN)
    c.box(460, 500, 400, 110, "Recursos protegidos", "projects, evaluate, dashboard…", SOFT, BORDER)

    c.group(980, 90, 380, 560, "Persistência")
    c.box(1020, 220, 300, 120, "Employee", "password_hash|company_id", outline=CYAN)
    c.box(1020, 420, 300, 120, "Neon PostgreSQL", "dados da organização", SOFT, BORDER)

    c.arrow(310, 210, 460, 210, "POST")
    c.arrow(660, 270, 190, 340, "token")
    c.arrow(310, 390, 460, 390)
    c.arrow(310, 550, 460, 550)
    c.arrow(860, 215, 1020, 270, "grava / lê")
    c.arrow(860, 555, 1020, 480)
    c.save("figura_05_fluxo_autenticacao")


def compose_screenshot(figura_n: int, stem: str, title: str, src_name: str, caption: str) -> None:
    src = FOTOS / src_name
    if not src.is_file():
        raise FileNotFoundError(src)

    shot = Image.open(src).convert("RGB")
    # Fit into max width while keeping aspect
    max_w, max_h = 1280, 720
    ratio = min(max_w / shot.width, max_h / shot.height)
    new_size = (max(1, int(shot.width * ratio)), max(1, int(shot.height * ratio)))
    shot = shot.resize(new_size, Image.Resampling.LANCZOS)

    pad_x, top, bottom = 40, 70, 50
    w = new_size[0] + pad_x * 2
    h = new_size[1] + top + bottom
    img = Image.new("RGB", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    f_title = load_font(22, True)
    f_cap = load_font(12, False)

    tw = draw.textbbox((0, 0), title, font=f_title)
    draw.text(((w - (tw[2] - tw[0])) / 2, 18), title, fill=NAVY, font=f_title)

    # subtle frame
    x0, y0 = pad_x, top
    draw.rectangle((x0 - 2, y0 - 2, x0 + new_size[0] + 2, y0 + new_size[1] + 2), outline=BORDER, width=2)
    img.paste(shot, (x0, y0))

    cw = draw.textbbox((0, 0), caption, font=f_cap)
    draw.text(((w - (cw[2] - cw[0])) / 2, h - 32), caption, fill=MUTED, font=f_cap)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"figura_{figura_n:02d}_{stem}.png"
    img.save(out, "PNG")
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


def write_readme() -> None:
    text = """# Figuras do TCC — SADS

Arquivos gerados em `docs/TCC/figuras/` (PNG prontos para Word).

| Figura | Arquivo | Conteúdo |
|--------|---------|----------|
| 1 | `figura_01_contexto_sads.png` | Diagrama de contexto |
| 2 | `figura_02_fluxo_recomendacao.png` | Fluxo evaluate / recomendação |
| 3 | `figura_03_pipeline_agentes.png` | Pipeline de agentes |
| 4 | `figura_04_er_simplificado.png` | ER simplificado |
| 5 | `figura_05_fluxo_autenticacao.png` | Auth + Bearer + API |
| 6 | `figura_06_landing.png` | Screenshot landing |
| 7 | `figura_07_dashboard.png` | Screenshot dashboard |
| 8 | `figura_08_project_new.png` | Screenshot novo projeto |
| 9 | `figura_09_project_evaluate.png` | Screenshot avaliação |

Scripts:
- `scripts/render_figura_01_contexto.py`
- `scripts/render_figuras_tcc_2_a_9.py`
"""
    (OUT_DIR / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    figura_02()
    figura_03()
    figura_04()
    figura_05()
    compose_screenshot(
        6,
        "landing",
        "Figura 6 — Landing institucional do SADS",
        "01_landing.png",
        "Fonte: Captura do sistema (2026).",
    )
    compose_screenshot(
        7,
        "dashboard",
        "Figura 7 — Painel (dashboard) autenticado",
        "02_dashboard.png",
        "Fonte: Captura do sistema (2026).",
    )
    compose_screenshot(
        8,
        "project_new",
        "Figura 8 — Tela de novo projeto / upload",
        "03_project_new.png",
        "Fonte: Captura do sistema (2026).",
    )
    compose_screenshot(
        9,
        "project_evaluate",
        "Figura 9 — Relatório de avaliação (project-evaluate)",
        "07_project_evaluate.png",
        "Fonte: Captura do sistema (2026).",
    )
    write_readme()
    print("OK — Figuras 2 a 9 geradas.")


if __name__ == "__main__":
    main()
