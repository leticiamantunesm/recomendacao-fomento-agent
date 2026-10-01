"""Gera apresentacao TC1 SADS (PPTX 16:9 + PDF via imagens + checklist).

Uso:
  python -m scripts.generate_tc1_presentation
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt
from pptx.oxml import parse_xml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "TCC" / "apresentacao_tc1"
ASSETS = OUT / "assets"

# Identidade SADS
NAVY = RGBColor(0x07, 0x0B, 0x2E)
NAVY_DEEP = RGBColor(0x04, 0x07, 0x1F)
NAVY_CARD = RGBColor(0x0C, 0x12, 0x38)
CYAN = RGBColor(0x2E, 0xC7, 0xFF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MUTED = RGBColor(0x9A, 0xA8, 0xC7)
LINE = RGBColor(0x1A, 0x2A, 0x55)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _set_run(run, *, size=18, bold=False, color=WHITE, font="Calibri"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def add_bg(slide, color=NAVY_DEEP):
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def add_accent_bar(slide):
    bar = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, 0, SLIDE_W, Inches(0.06)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN
    bar.line.fill.background()


def add_text(
    slide,
    text,
    left,
    top,
    width,
    height,
    *,
    size=18,
    bold=False,
    color=WHITE,
    align=PP_ALIGN.LEFT,
    font="Calibri",
):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    _set_run(run, size=size, bold=bold, color=color, font=font)
    return box


def add_notes(slide, text: str):
    notes = slide.notes_slide.notes_text_frame
    notes.clear()
    notes.text = text.strip()


def card(slide, left, top, width, height, fill=NAVY_CARD):
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = LINE
    shape.line.width = Pt(1)
    try:
        shape.adjustments[0] = 0.08
    except Exception:
        pass
    return shape


def chip(slide, left, top, width, height, text):
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = NAVY_CARD
    shape.line.color.rgb = CYAN
    shape.line.width = Pt(1)
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    _set_run(run, size=14, bold=True, color=CYAN)
    return shape


def flow_box(slide, left, top, width, height, title, subtitle=""):
    shape = card(slide, left, top, width, height)
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = title
    _set_run(run, size=14, bold=True, color=WHITE)
    if subtitle:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = subtitle
        _set_run(r2, size=11, color=MUTED)
    return shape


def arrow_right(slide, left, top):
    add_text(slide, "→", left, top, Inches(0.4), Inches(0.35), size=20, bold=True, color=CYAN, align=PP_ALIGN.CENTER)


def logo(slide, left=Inches(0.5), top=Inches(0.25), height=Inches(0.7)):
    path = ASSETS / "sads-logo.png"
    if path.exists():
        slide.shapes.add_picture(str(path), left, top, height=height)


def build() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    # ---------- SLIDE 1 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    logo(s, Inches(0.7), Inches(0.9), Inches(1.1))
    add_text(s, "SADS", Inches(0.7), Inches(2.2), Inches(12), Inches(0.8), size=40, bold=True, color=CYAN)
    add_text(
        s,
        "Sistema de Apoio à Decisão para Fomento à Inovação",
        Inches(0.7),
        Inches(2.95),
        Inches(11.5),
        Inches(0.6),
        size=24,
        bold=True,
        color=WHITE,
    )
    add_text(
        s,
        "Uma plataforma inteligente para conectar projetos de inovação aos mecanismos de fomento mais aderentes.",
        Inches(0.7),
        Inches(3.7),
        Inches(10.5),
        Inches(0.7),
        size=16,
        color=MUTED,
    )
    add_text(
        s,
        "TC1 · Ciência da Computação · Universidade Paulista (UNIP) — Paraíso · 2026",
        Inches(0.7),
        Inches(5.0),
        Inches(11),
        Inches(0.4),
        size=14,
        color=MUTED,
    )
    add_text(
        s,
        "Letícia Melo  ·  Filipe Ribeiro  ·  Fabiano Rocha  ·  Ruben Pereira  ·  Victor Yukio",
        Inches(0.7),
        Inches(5.45),
        Inches(12),
        Inches(0.4),
        size=15,
        color=WHITE,
    )
    add_notes(
        s,
        """SLIDE 1 — Abertura (~30s)

Bom dia / boa tarde. Somos o grupo de Ciência da Computação da UNIP e apresentamos o SADS —
Sistema de Apoio à Decisão para Fomento à Inovação.

Em uma frase: trata-se de uma plataforma inteligente para conectar projetos de inovação
aos mecanismos de fomento mais aderentes.

Esta é a defesa do TC1, preparação para o TCC final. Nos próximos minutos mostramos o
contexto, o problema, a solução, o protótipo e os próximos passos.""",
    )

    # ---------- SLIDE 2 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    add_text(s, "01  CONTEXTO", Inches(0.6), Inches(0.3), Inches(4), Inches(0.35), size=12, bold=True, color=CYAN)
    add_text(
        s,
        "Inovar exige investimento e acesso aos mecanismos certos",
        Inches(0.6),
        Inches(0.7),
        Inches(12),
        Inches(0.7),
        size=28,
        bold=True,
        color=WHITE,
    )
    add_text(
        s,
        "O ecossistema brasileiro oferece oferece fontes de apoio financeiro e estratégico — mas elas estão dispersas.",
        Inches(0.6),
        Inches(1.45),
        Inches(12),
        Inches(0.45),
        size=16,
        color=MUTED,
    )

    boxes = [
        ("Projetos de\ninovação", Inches(0.6)),
        ("Instituições\nFINEP · FAPESP\nBNDES · EMBRAPII", Inches(3.5)),
        ("Mecanismos\nEditais · Subvenção\nFinanciamento · Fiscais", Inches(6.7)),
        ("Critérios e\nprocessos\ndistintos", Inches(10.0)),
    ]
    for i, (label, left) in enumerate(boxes):
        flow_box(s, left, Inches(2.4), Inches(2.6), Inches(2.0), label)
        if i < 3:
            arrow_right(s, left + Inches(2.65), Inches(3.15))

    chip(s, Inches(0.6), Inches(5.0), Inches(12.1), Inches(0.9), "")
    add_text(
        s,
        "Mensagem: o desafio não é só a ausência de recursos — é identificar e acessar o mecanismo adequado.",
        Inches(0.85),
        Inches(5.15),
        Inches(11.6),
        Inches(0.6),
        size=16,
        bold=True,
        color=WHITE,
    )
    add_notes(
        s,
        """SLIDE 2 — Contexto (~60s)

O Brasil possui um ecossistema rico de fomento: editais públicos, subvenção econômica,
financiamentos, incentivos fiscais e parcerias com ICTs, com instituições como FINEP,
FAPESP, BNDES e EMBRAPII.

O ponto não é que “não existam oportunidades”. Elas existem — porém estão distribuídas
entre instituições, programas e critérios diferentes.

O fluxo ilustra isso: projetos de inovação atravessam instituições, mecanismos e processos
distintos. Por isso, escolher o caminho certo exige informação estruturada.""",
    )

    # ---------- SLIDE 3 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    add_text(s, "02  PROBLEMA", Inches(0.6), Inches(0.3), Inches(4), Inches(0.35), size=12, bold=True, color=CYAN)
    add_text(
        s,
        "Encontrar o mecanismo adequado ainda é um processo complexo",
        Inches(0.6),
        Inches(0.7),
        Inches(12),
        Inches(0.65),
        size=26,
        bold=True,
        color=WHITE,
    )

    pains = [
        "Fragmentação das informações",
        "Desconhecimento das oportunidades",
        "Critérios de elegibilidade complexos",
        "Dificuldade de comparar programas",
        "Alto esforço para interpretar editais",
        "Dependência de especialistas",
    ]
    for i, pain in enumerate(pains):
        col = i % 3
        row = i // 3
        left = Inches(0.6) + Inches(4.1) * col
        top = Inches(1.55) + Inches(0.85) * row
        card(s, left, top, Inches(3.9), Inches(0.7))
        add_text(s, pain, left + Inches(0.2), top + Inches(0.18), Inches(3.5), Inches(0.4), size=14, color=WHITE)

    add_text(s, "Jornada atual (pontos de atrito)", Inches(0.6), Inches(3.5), Inches(8), Inches(0.35), size=14, bold=True, color=CYAN)
    steps = ["Buscar", "Ler editais", "Interpretar", "Comparar", "Adaptar", "Submeter"]
    for i, st in enumerate(steps):
        left = Inches(0.6) + Inches(2.05) * i
        flow_box(s, left, Inches(4.0), Inches(1.85), Inches(0.95), st)
        if i < 5:
            arrow_right(s, left + Inches(1.85), Inches(4.25))

    add_text(
        s,
        "Referência no projeto (SADS.pdf): consultorias — R$ 1 mil a R$ 5 mil por análise; comissão de êxito 0,5%–2% (até 3–5%). Não é estatística conclusiva.",
        Inches(0.6),
        Inches(5.35),
        Inches(12),
        Inches(0.7),
        size=13,
        color=MUTED,
    )
    add_text(
        s,
        "Decisão hoje: manual, fragmentada, demorada e dependente de conhecimento especializado.",
        Inches(0.6),
        Inches(6.15),
        Inches(12),
        Inches(0.45),
        size=15,
        bold=True,
        color=WHITE,
    )
    add_notes(
        s,
        """SLIDE 3 — Problema (~70s)

Na prática, gestores enfrentam fragmentação, desconhecimento, critérios complexos e
dificuldade de comparar programas. Interpretar editais exige tempo; muitos dependem de
consultorias; há risco de investir esforço em oportunidades incompatíveis.

A jornada atual — buscar, ler, interpretar, comparar, adaptar e submeter — concentra atritos
em quase todas as etapas.

No material do projeto (SADS.pdf) aparecem referências a custos de consultoria: cerca de
R$ 1 mil a R$ 5 mil por análise, e comissão de êxito tipicamente entre 0,5% e 2%, podendo
chegar a 3–5%. Tratamos esses valores como referência apresentada no projeto, não como
pesquisa estatística conclusiva.

Em síntese: a tomada de decisão continua manual, fragmentada e especializada.""",
    )

    # ---------- SLIDE 4 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    add_text(s, "03  QUESTÃO E OBJETIVO", Inches(0.6), Inches(0.3), Inches(5), Inches(0.35), size=12, bold=True, color=CYAN)
    add_text(
        s,
        "Como apoiar uma decisão mais rápida, consistente e explicável?",
        Inches(0.6),
        Inches(0.7),
        Inches(12),
        Inches(0.7),
        size=26,
        bold=True,
        color=WHITE,
    )
    card(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(1.35))
    add_text(
        s,
        "Questão norteadora",
        Inches(0.85),
        Inches(1.75),
        Inches(11),
        Inches(0.3),
        size=13,
        bold=True,
        color=CYAN,
    )
    add_text(
        s,
        "Como utilizar dados e inteligência artificial para recomendar mecanismos de fomento compatíveis com o perfil de uma empresa e de seu projeto de inovação?",
        Inches(0.85),
        Inches(2.15),
        Inches(11.5),
        Inches(0.6),
        size=16,
        color=WHITE,
    )

    card(s, Inches(0.6), Inches(3.2), Inches(12.1), Inches(1.2))
    add_text(s, "Objetivo geral", Inches(0.85), Inches(3.35), Inches(11), Inches(0.3), size=13, bold=True, color=CYAN)
    add_text(
        s,
        "Desenvolver um sistema de apoio à decisão capaz de analisar empresas e projetos, comparar critérios de programas de fomento e gerar recomendações classificadas e explicáveis.",
        Inches(0.85),
        Inches(3.75),
        Inches(11.5),
        Inches(0.55),
        size=15,
        color=WHITE,
    )

    objs = [
        ("1", "Estruturar informações\nde empresas, projetos\ne programas"),
        ("2", "Avaliar elegibilidade\ne aderência"),
        ("3", "Apresentar ranking,\njustificativas e lacunas"),
    ]
    for i, (n, t) in enumerate(objs):
        left = Inches(0.6) + Inches(4.1) * i
        card(s, left, Inches(4.7), Inches(3.9), Inches(1.55))
        add_text(s, n, left + Inches(0.25), Inches(4.85), Inches(0.5), Inches(0.35), size=20, bold=True, color=CYAN)
        add_text(s, t, left + Inches(0.25), Inches(5.3), Inches(3.4), Inches(0.8), size=14, color=WHITE)

    add_notes(
        s,
        """SLIDE 4 — Questão e objetivo (~60s)

A questão que orienta o trabalho é: como usar dados e IA para recomendar mecanismos de
fomento compatíveis com o perfil da empresa e do projeto?

O objetivo geral é desenvolver um sistema de apoio à decisão que analise empresas e
projetos, compare critérios e gere recomendações classificadas e explicáveis.

Especificamente: estruturar informações; avaliar elegibilidade e aderência; e apresentar
ranking, justificativas e lacunas.

Importante: o SADS não substitui a decisão humana — organiza informação e apoia a decisão.""",
    )

    # ---------- SLIDE 5 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    add_text(s, "04  SOLUÇÃO", Inches(0.6), Inches(0.3), Inches(4), Inches(0.35), size=12, bold=True, color=CYAN)
    add_text(
        s,
        "SADS: recomendação inteligente e explicável de fomento",
        Inches(0.6),
        Inches(0.7),
        Inches(12),
        Inches(0.6),
        size=26,
        bold=True,
        color=WHITE,
    )
    add_text(
        s,
        "Plataforma SaaS multi-tenant (conforme proposta do projeto) com análise de perfil + PDF e saída em ranking explicável.",
        Inches(0.6),
        Inches(1.35),
        Inches(12),
        Inches(0.4),
        size=15,
        color=MUTED,
    )

    flow = [
        ("Empresa\n+ Projeto", Inches(0.5)),
        ("Análise e\nestruturação", Inches(3.1)),
        ("Regras e\ncritérios", Inches(5.7)),
        ("Motor de\nrecomendação", Inches(8.3)),
        ("Ranking +\nrelatório", Inches(10.9)),
    ]
    for i, (label, left) in enumerate(flow):
        flow_box(s, left, Inches(2.1), Inches(2.2), Inches(1.5), label)
        if i < 4:
            arrow_right(s, left + Inches(2.2), Inches(2.65))

    benefits = [
        ("Centralização", "Visão unificada dos mecanismos"),
        ("Menos esforço", "Reduz triagem manual de editais"),
        ("Personalização", "Aderência ao perfil e ao projeto"),
        ("Transparência", "Score e justificativas por critério"),
        ("Planejamento", "Lacunas e próximos passos"),
    ]
    for i, (t, d) in enumerate(benefits):
        left = Inches(0.5) + Inches(2.5) * i
        card(s, left, Inches(4.1), Inches(2.35), Inches(2.0))
        add_text(s, t, left + Inches(0.15), Inches(4.3), Inches(2.05), Inches(0.4), size=14, bold=True, color=CYAN)
        add_text(s, d, left + Inches(0.15), Inches(4.8), Inches(2.05), Inches(1.0), size=13, color=WHITE)

    add_notes(
        s,
        """SLIDE 5 — Solução (~70s)

O SADS é proposto como plataforma SaaS multi-tenant: recebe o perfil da empresa e o PDF do
projeto; estrutura características; compara com critérios de programas; gera ranking de
aderência; explica resultados; identifica lacunas; e sugere próximos passos.

O fluxo central é: Empresa + Projeto → análise → regras → motor → ranking e relatório.

Os benefícios esperados são centralização, redução de esforço, personalização, transparência
e apoio ao planejamento da submissão — sempre como suporte à decisão.""",
    )

    # ---------- SLIDE 6 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    add_text(s, "05  PROTÓTIPO", Inches(0.6), Inches(0.25), Inches(4), Inches(0.3), size=12, bold=True, color=CYAN)
    add_text(
        s,
        "Da submissão do projeto à recomendação",
        Inches(0.6),
        Inches(0.55),
        Inches(10),
        Inches(0.5),
        size=26,
        bold=True,
        color=WHITE,
    )

    shots = [
        (ASSETS / "screen_landing.png", "1. Landing", True),
        (ASSETS / "screen_register.png", "2. Cadastro / conta", True),
        (ASSETS / "screen_login.png", "3. Login", True),
        (ASSETS / "screen_report.png", "4. Relatório (demo)", True),
    ]
    for i, (path, label, implemented) in enumerate(shots):
        left = Inches(0.4) + Inches(3.25) * i
        card(s, left, Inches(1.2), Inches(3.1), Inches(3.55))
        if path.exists():
            # fit image inside card
            s.shapes.add_picture(str(path), left + Inches(0.12), Inches(1.35), width=Inches(2.85))
        add_text(
            s,
            label,
            left + Inches(0.1),
            Inches(4.4),
            Inches(2.9),
            Inches(0.3),
            size=12,
            bold=True,
            color=CYAN if implemented else MUTED,
            align=PP_ALIGN.CENTER,
        )

    add_text(
        s,
        "Implementado no protótipo atual: landing, registro/login, upload de PDF, scoring FINEP e relatório explicável.",
        Inches(0.5),
        Inches(5.0),
        Inches(12.3),
        Inches(0.4),
        size=14,
        color=WHITE,
    )
    add_text(
        s,
        "Visão futura / a evoluir: SSO corporativo completo, catálogo multi-fonte em produção contínua, chat (Fase B), validação com usuários.",
        Inches(0.5),
        Inches(5.45),
        Inches(12.3),
        Inches(0.45),
        size=13,
        color=MUTED,
    )
    add_text(
        s,
        "Valor central do relatório: ranking · score · critérios · lacunas · plano de ação",
        Inches(0.5),
        Inches(6.1),
        Inches(12.3),
        Inches(0.4),
        size=15,
        bold=True,
        color=CYAN,
    )
    add_notes(
        s,
        """SLIDE 6 — Protótipo (~90s)

Mostramos a jornada no protótipo existente. Há landing pública; cadastro da organização e do
usuário administrador; login com senha; upload do PDF do projeto; processamento com
cruzamento do corpus FINEP; e relatório com ranking, score, critérios, lacunas e plano de ação.

O relatório é o principal valor entregue: não apenas “qual edital”, mas por quê — e o que falta.

Separação importante: o que já está no protótipo versus o que é visão futura — SSO corporativo
completo, catálogo multi-fonte contínuo, chat (Fase B) e validação formal com usuários ainda
são etapas a consolidar no TCC.""",
    )

    # ---------- SLIDE 7 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    add_text(s, "06  ARQUITETURA", Inches(0.6), Inches(0.25), Inches(4), Inches(0.3), size=12, bold=True, color=CYAN)
    add_text(s, "Arquitetura proposta", Inches(0.6), Inches(0.55), Inches(10), Inches(0.5), size=28, bold=True, color=WHITE)

    layers = [
        ("Interface", "React / Next.js\nTailwind CSS\n(landing já em Next)"),
        ("Backend &\nautenticação", "Proposta: Node/Express + Auth.js/OAuth\nPoC atual: FastAPI + sessão/senha\n(a convergir no TCC)"),
        ("Dados", "PostgreSQL (+ pgvector)\nempresas · usuários · projetos\nprogramas · critérios · logs"),
        ("Motor de\nrecomendação", "NLP / extração\nRegras de elegibilidade\nAHP · TOPSIS · LLM (explicação)"),
    ]
    for i, (title, body) in enumerate(layers):
        top = Inches(1.25) + Inches(1.35) * i
        card(s, Inches(0.6), top, Inches(12.1), Inches(1.2))
        add_text(s, title, Inches(0.85), top + Inches(0.2), Inches(3.2), Inches(0.8), size=16, bold=True, color=CYAN)
        add_text(s, body, Inches(4.2), top + Inches(0.2), Inches(8.2), Inches(0.9), size=14, color=WHITE)

    add_notes(
        s,
        """SLIDE 7 — Arquitetura (~80s)

A arquitetura proposta no material do projeto organiza quatro camadas: interface; backend e
autenticação; dados; e motor de recomendação.

Na interface: React/Next e Tailwind — a landing já usa Next.js.

No backend: a proposta do SADS.pdf aponta Node/Express e Auth.js/OAuth; o protótipo atual
do TC1 usa FastAPI com autenticação por senha e token — convergência prevista no TCC.

Nos dados: PostgreSQL, no nosso caso com pgvector no Neon.

No motor: combinar NLP para extração, regras determinísticas para elegibilidade objetiva,
métodos multicritério (AHP para pesos, TOPSIS para ranking) e LLM para apoio à interpretação
e explicabilidade — sem tratar IA como caixa-preta que decide sozinha.

Mensagem: regras + multicritério + IA = recomendações auditáveis.""",
    )

    # ---------- SLIDE 8 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    add_text(s, "07  CONFIABILIDADE", Inches(0.6), Inches(0.25), Inches(5), Inches(0.3), size=12, bold=True, color=CYAN)
    add_text(
        s,
        "Uma recomendação útil precisa ser confiável",
        Inches(0.6),
        Inches(0.55),
        Inches(12),
        Inches(0.5),
        size=26,
        bold=True,
        color=WHITE,
    )

    columns = [
        (
            "Diferenciais",
            [
                "Recomendação personalizada",
                "Score explicável",
                "Visão unificada",
                "Histórico de análises",
                "Lacunas e plano de ação",
            ],
        ),
        (
            "Segurança e LGPD",
            [
                "LGPD (finalidade/minimização)",
                "RBAC / papéis",
                "Isolamento multi-tenant",
                "OAuth 2.0 (roadmap)",
                "SSL/TLS e logs de auditoria",
            ],
        ),
        (
            "Limitações atuais",
            [
                "Catálogo precisa atualização",
                "Regras extraídas exigem validação",
                "Não garante aprovação",
                "Apoia — não substitui — especialistas",
                "Editais e critérios mudam",
            ],
        ),
    ]
    for i, (title, items) in enumerate(columns):
        left = Inches(0.5) + Inches(4.2) * i
        card(s, left, Inches(1.3), Inches(4.0), Inches(5.3))
        add_text(s, title, left + Inches(0.25), Inches(1.5), Inches(3.5), Inches(0.4), size=16, bold=True, color=CYAN)
        for j, item in enumerate(items):
            add_text(
                s,
                "•  " + item,
                left + Inches(0.25),
                Inches(2.15) + Inches(0.7) * j,
                Inches(3.5),
                Inches(0.55),
                size=14,
                color=WHITE,
            )

    add_notes(
        s,
        """SLIDE 8 — Diferenciais, segurança e limitações (~60s)

Diferenciais: personalização, explicabilidade, visão unificada, histórico, lacunas e plano de ação.

Segurança e privacidade: alinhamento a LGPD, controle por papéis, multi-tenant, OAuth no
roadmap, trânsito protegido e logs.

Limitações — e aqui demonstramos maturidade acadêmica: a qualidade depende do catálogo;
regras precisam validação; recomendação não garante aprovação; o sistema apoia gestores e
especialistas, não os substitui; e o cenário regulatório muda.

Isso deixa claro o que o TC1 entrega e o que o TCC ainda precisa amadurecer.""",
    )

    # ---------- SLIDE 9 ----------
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_accent_bar(s)
    add_text(s, "08  ENCERRAMENTO", Inches(0.6), Inches(0.25), Inches(5), Inches(0.3), size=12, bold=True, color=CYAN)
    add_text(s, "Próximos passos para o TCC", Inches(0.6), Inches(0.55), Inches(12), Inches(0.5), size=28, bold=True, color=WHITE)

    timeline = [
        ("Req. &\ndados", "Refinar requisitos\ne modelo"),
        ("Catálogo", "Coleta e atualização\nde programas"),
        ("Motor", "Elegibilidade +\nAHP/TOPSIS/LLM"),
        ("Validação", "Usuários, testes\ne segurança"),
        ("Entrega", "Avaliar qualidade\ne documentar"),
    ]
    for i, (t, d) in enumerate(timeline):
        left = Inches(0.5) + Inches(2.5) * i
        flow_box(s, left, Inches(1.35), Inches(2.3), Inches(1.7), t, d)
        if i < 4:
            arrow_right(s, left + Inches(2.3), Inches(1.95))

    add_text(s, "Critérios de sucesso (TCC)", Inches(0.6), Inches(3.4), Inches(8), Inches(0.35), size=14, bold=True, color=CYAN)
    criteria = [
        "Identificar programas elegíveis",
        "Gerar ranking justificável",
        "Usuário compreende o porquê",
        "Detectar informações ausentes",
        "Concluir o fluxo principal de ponta a ponta",
    ]
    for i, c in enumerate(criteria):
        left = Inches(0.6) + Inches(2.5) * i
        card(s, left, Inches(3.85), Inches(2.35), Inches(1.35))
        add_text(s, c, left + Inches(0.12), Inches(4.05), Inches(2.1), Inches(1.0), size=12, color=WHITE, align=PP_ALIGN.CENTER)

    add_text(
        s,
        "O SADS transforma informações fragmentadas em uma decisão estruturada, explicável e orientada ao projeto.",
        Inches(0.6),
        Inches(5.5),
        Inches(12.1),
        Inches(0.5),
        size=15,
        bold=True,
        color=WHITE,
    )
    add_text(
        s,
        "Obrigado. Espaço para perguntas.",
        Inches(0.6),
        Inches(6.2),
        Inches(12),
        Inches(0.4),
        size=18,
        bold=True,
        color=CYAN,
    )
    add_notes(
        s,
        """SLIDE 9 — Próximos passos e encerramento (~40s)

Para o TCC: refinar requisitos e dados; consolidar coleta de programas; evoluir o motor
(regras, AHP/TOPSIS, LLM); validar com usuários; testar funcionalmente e em segurança;
avaliar qualidade das recomendações; e documentar resultados e limitações.

Critérios de sucesso: elegibilidade correta; ranking justificável; compreensão do usuário;
detecção de lacunas; e fluxo ponta a ponta.

Fechamos com a tese do trabalho: o SADS transforma informação fragmentada em decisão
estruturada, explicável e orientada ao projeto.

Obrigado — ficamos à disposição para perguntas.""",
    )

    pptx_path = OUT / "SADS_TC1_Apresentacao.pptx"
    prs.save(str(pptx_path))
    return pptx_path


def export_pdf_from_pptx(pptx_path: Path) -> Path | None:
    """Tenta exportar PDF via PowerPoint COM (Windows)."""
    pdf_path = pptx_path.with_suffix(".pdf")
    try:
        import win32com.client  # type: ignore
    except Exception:
        # fallback: gerar PDF simples com PyMuPDF a partir de texto+capas
        return _pdf_fallback(pptx_path)
    try:
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        powerpoint.Visible = 1
        presentation = powerpoint.Presentations.Open(str(pptx_path.resolve()), WithWindow=False)
        presentation.SaveAs(str(pdf_path.resolve()), 32)  # 32 = ppSaveAsPDF
        presentation.Close()
        powerpoint.Quit()
        return pdf_path
    except Exception:
        return _pdf_fallback(pptx_path)


def _pdf_fallback(pptx_path: Path) -> Path:
    """PDF de revisão com roteiro + metadados (quando PowerPoint COM indisponível)."""
    import fitz

    pdf_path = pptx_path.with_name("SADS_TC1_Apresentacao_roteiro.pdf")
    doc = fitz.open()
    # cover
    page = doc.new_page(width=595, height=842)
    page.draw_rect(page.rect, color=(0.02, 0.03, 0.12), fill=(0.02, 0.03, 0.12))
    page.insert_text((50, 80), "SADS — TC1", fontsize=24, color=(0.18, 0.78, 1))
    page.insert_text((50, 120), "Apresentação acadêmica (roteiro oral + checklist)", fontsize=14, color=(1, 1, 1))
    page.insert_text((50, 160), "Arquivo editável: SADS_TC1_Apresentacao.pptx", fontsize=11, color=(0.7, 0.75, 0.85))
    page.insert_text((50, 190), "Use o PPTX para a defesa. Este PDF resume o roteiro.", fontsize=11, color=(0.7, 0.75, 0.85))

    notes_by_slide = []
    # extract notes from pptx via python-pptx
    from pptx import Presentation as P

    prs = P(str(pptx_path))
    for i, slide in enumerate(prs.slides, 1):
        notes = ""
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text
        notes_by_slide.append((i, notes))

    for i, notes in notes_by_slide:
        page = doc.new_page(width=595, height=842)
        page.draw_rect(page.rect, color=(1, 1, 1), fill=(1, 1, 1))
        page.insert_text((40, 40), f"Roteiro — Slide {i}", fontsize=16, color=(0.04, 0.05, 0.18))
        y = 70
        for line in notes.splitlines():
            if y > 800:
                page = doc.new_page(width=595, height=842)
                y = 40
            page.insert_text((40, y), line[:110], fontsize=10, color=(0.1, 0.1, 0.15))
            y += 14

    # checklist page
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "Checklist final", fontsize=16, color=(0.04, 0.05, 0.18))
    checklist = Path(OUT / "CHECKLIST_TC1.md").read_text(encoding="utf-8") if (OUT / "CHECKLIST_TC1.md").exists() else ""
    y = 70
    for line in checklist.splitlines():
        if y > 800:
            break
        page.insert_text((40, y), line[:110], fontsize=9, color=(0.1, 0.1, 0.15))
        y += 12

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def write_checklist() -> Path:
    path = OUT / "CHECKLIST_TC1.md"
    path.write_text(
        """# Checklist da apresentação TC1 — SADS

## Tempo previsto por slide

| Slide | Título | Tempo |
|------:|--------|------:|
| 1 | Abertura | 30 s |
| 2 | Contexto | 60 s |
| 3 | Problema | 70 s |
| 4 | Questão e objetivo | 60 s |
| 5 | Solução | 70 s |
| 6 | Protótipo e UX | 90 s |
| 7 | Arquitetura | 80 s |
| 8 | Diferenciais / segurança / limitações | 60 s |
| 9 | Próximos passos e encerramento | 40 s |
| | **Total estimado** | **≈ 9 min 20 s** |

Folga restante (~40 s) para perguntas iniciais ou transição.

## Informações a confirmar / a validar

- [ ] Datas e sala da banca TC1
- [ ] Ordem de fala dos integrantes (quem apresenta cada bloco)
- [ ] Se o professor espera ênfase em APS Sem. 07 vs. protótipo atual
- [ ] Valores de consultoria do SADS.pdf: usar apenas como referência do material (não como estatística)
- [ ] Nomenclatura institucional exata nos slides (turma CC7P68/CC6P68)
- [ ] Escopo FINEP no PoC atual vs. multi-fonte proposta (deixar explícito na fala do slide 6/7)
- [ ] Status real de SSO/OAuth (roadmap — não apresentar como pronto)
- [ ] Métricas de acerto do scoring em produção: **ainda a validar** com usuários

## Capturas de tela do protótipo (usadas / recomendadas)

Já incluídas em `assets/`:

- `screen_landing.png` — landing pública
- `screen_register.png` — cadastro da organização
- `screen_login.png` — login
- `screen_report.png` — seção de demonstração do relatório

Recomendado capturar antes da banca (melhor resolução desktop 1440px):

- [ ] `project-new.html` — upload de PDF
- [ ] `project-evaluate.html` — relatório real pós-avaliação (não só mock da landing)
- [ ] `dashboard.html` — painel autenticado com métricas
- [ ] Fluxo completo com projeto SEMENTE VIVA (caso de teste do grupo)

## Revisão crítica (pré-banca)

- [x] Cabe em ~10 minutos
- [x] Problema claro e distinto do contexto
- [x] Protótipo aparece (slide 6) com separação pronto vs. futuro
- [x] Solução responde ao problema
- [x] Arquitetura legível; PoC atual vs. proposta do PDF sinalizados
- [x] Sem métricas inventadas de validação de usuário
- [x] Slides concisos
- [x] Contribuição acadêmica (apoio à decisão + explicabilidade + limitações)
- [x] Funcionalidades atuais ≠ futuras

## Arquivos gerados

- `SADS_TC1_Apresentacao.pptx` — apresentação editável (usar na defesa)
- `SADS_TC1_Apresentacao_roteiro.pdf` — PDF de revisão com roteiro oral
- `CHECKLIST_TC1.md` — este arquivo
- `assets/` — logo e screenshots
""",
        encoding="utf-8",
    )
    return path


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    checklist = write_checklist()
    pptx = build()
    pdf = export_pdf_from_pptx(pptx)
    print("PPTX:", pptx)
    print("PDF :", pdf)
    print("CHECKLIST:", checklist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
