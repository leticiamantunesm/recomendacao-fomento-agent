# -*- coding: utf-8 -*-
"""Gera Word intermediário para apresentação TC1."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path(__file__).resolve().parents[1] / "docs" / "SADS_Guia_Intermediario_Apresentacao.docx"

doc = Document()
for section in doc.sections:
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

NAVY = RGBColor(0x07, 0x0B, 0x2E)
CYAN = RGBColor(0x0C, 0x6E, 0xA8)
GRAY = RGBColor(0x55, 0x55, 0x55)


def set_run_font(run, size=11, bold=False, color=None):
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color


def add_heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        set_run_font(
            run,
            size=16 if level == 1 else (13 if level == 2 else 12),
            bold=True,
            color=NAVY,
        )
    return h


def add_p(text, *, bold=False, size=11, space_after=8, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, color=RGBColor(0x1A, 0x1A, 0x1A))
    run.italic = italic
    return p


def add_bullets(items, size=11):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(item)
        set_run_font(run, size=size)


def add_fala(titulo, texto):
    add_p(titulo, bold=True, size=11, space_after=2)
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run(texto)
    set_run_font(run, size=11)
    run.italic = True


# Capa
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("SADS")
set_run_font(r, size=28, bold=True, color=NAVY)

st = doc.add_paragraph()
st.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = st.add_run("Sistema de Apoio à Decisão para Fomento à Inovação")
set_run_font(r, size=14, bold=True, color=NAVY)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("Guia intermediário para o grupo · Preparação da apresentação TC1")
set_run_font(r, size=12, color=CYAN)

meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = meta.add_run(
    "Baseado em docs/MANUAL_COMPLETO_SADS.md e docs/ARQUITETURA_SADS.md\n"
    "Versão 1.0 · 30/09/2026 · Ciência da Computação · UNIP Paraíso\n"
    "Integrantes: Letícia Melo · Filipe Ribeiro · Fabiano Rocha · Ruben Pereira · Victor Yukio"
)
set_run_font(r, size=10, color=GRAY)

add_p(
    "Este documento é mais detalhado que o RESUMO_GRUPO_SADS.md: traz arquitetura, "
    "agentes, segurança, status de implementação e textos prontos para falar na banca. "
    "Não substitui o manual completo — use-o para estudar e ensaiar.",
    italic=True,
    size=10,
)

add_heading("1. O que é o SADS e o que ele entrega", 1)
add_p(
    "O SADS é uma aplicação web de apoio à decisão que ajuda empresas e gestores a "
    "identificar mecanismos de fomento compatíveis com o perfil da organização e com "
    "o conteúdo de um projeto de inovação (enviado em PDF)."
)
add_p("A entrega principal ao usuário é um relatório com:", bold=True)
add_bullets(
    [
        "ranking de programas/chamadas (piloto atual: FINEP);",
        "score de aderência (0–100) com breakdown por critérios;",
        "forças, fraquezas e lacunas;",
        "plano de ação sugerido na interface;",
        "link para a página oficial da chamada, quando disponível.",
    ]
)
add_p(
    "O SADS não garante aprovação em editais, não faz a submissão oficial ao órgão "
    "e não substitui consultoria especializada ou parecer jurídico. Ele organiza a "
    "análise inicial de forma estruturada e explicável."
)
add_fala(
    "Fala recomendada (abertura conceitual — ~25 s)",
    "“O SADS é um sistema de apoio à decisão para fomento à inovação. A ideia é "
    "receber o perfil da empresa e o PDF do projeto, cruzar com um corpus de "
    "chamadas — no protótipo, a FINEP — e devolver um ranking acompanhado de "
    "justificativas e lacunas. O gestor continua sendo quem decide; o sistema "
    "reduz o esforço inicial de triagem.”",
)

add_heading("2. Problema de pesquisa e contexto", 1)
add_p(
    "Formulação acadêmica: como apoiar, de maneira estruturada e explicável, a "
    "identificação de mecanismos de fomento compatíveis com o perfil de uma "
    "organização e de seu projeto de inovação?"
)
add_p(
    "No Brasil existem diversas fontes de apoio (editais, subvenção, crédito, "
    "incentivos fiscais, parcerias com ICTs), com instituições como FINEP, FAPESP, "
    "BNDES e EMBRAPII. O problema não é apenas a ausência de recursos: as "
    "oportunidades estão dispersas, os critérios são complexos e comparar "
    "alternativas exige tempo e conhecimento especializado."
)
add_p("Dores que o sistema ataca:", bold=True)
add_bullets(
    [
        "fragmentação das informações;",
        "desconhecimento das oportunidades;",
        "dificuldade de interpretar e comparar editais;",
        "risco de investir esforço em chamada incompatível;",
        "dependência de especialistas e consultorias.",
    ]
)
add_fala(
    "Fala recomendada (problema — ~40 s)",
    "“A dificuldade não está apenas em encontrar um edital. É necessário interpretar "
    "critérios, verificar elegibilidade, comparar alternativas e entender como o "
    "projeto precisa ser estruturado. Hoje esse processo é manual, fragmentado e "
    "caro em tempo — e muitas vezes depende de quem já conhece o ecossistema.”",
)

add_heading("3. Objetivos (o que o grupo pode afirmar)", 1)
add_p("Objetivo geral:", bold=True)
add_p(
    "Desenvolver um sistema de apoio à decisão capaz de estruturar informações de "
    "empresas, projetos e programas de fomento, avaliar compatibilidade e apresentar "
    "recomendações justificáveis."
)
add_p("Objetivos específicos com status real:", bold=True)
add_bullets(
    [
        "Cadastrar organizações e usuários — IMPLEMENTADO (auth por senha).",
        "Receber e processar PDF do projeto — IMPLEMENTADO (extração parcial em PDF escaneado).",
        "Manter catálogo de chamadas — PARCIAL (piloto FINEP).",
        "Verificar elegibilidade e calcular aderência — IMPLEMENTADO (gates + matriz v2).",
        "Produzir ranking, justificativas e lacunas — IMPLEMENTADO.",
        "Histórico de aplicações — IMPLEMENTADO.",
        "SSO, RBAC fino, chat LLM, AHP/TOPSIS — PLANEJADOS para o TCC.",
    ]
)

add_heading("4. Jornada do usuário (do cadastro ao relatório)", 1)
add_p(
    "Landing → Criar conta ou Login → Painel → Novo projeto (upload PDF) → "
    "Revisão do formulário extraído → Avaliar → Relatório com ranking → "
    "(opcional) atualizar status em Aplicações."
)
add_p(
    "Em paralelo / antes: a equipe operacional alimenta o corpus FINEP "
    "(coleta → seed → embeddings no Neon). Sem corpus indexado, o evaluate não tem o que recomendar."
)
add_fala(
    "Fala recomendada (jornada — ~35 s)",
    "“Do ponto de vista do usuário, o fluxo é direto: autentica a organização, "
    "envia o PDF, revisa o que foi extraído e dispara a avaliação. O valor aparece "
    "no relatório — não só uma lista de editais, mas score, critérios, lacunas e "
    "link para a chamada oficial.”",
)

add_heading("5. Arquitetura (visão para a banca)", 1)
add_p(
    "Camadas reais do repositório: frontend (landing Next.js exportada + UI HTML/JS "
    "em web/), backend FastAPI (app/), banco Neon PostgreSQL com pgvector (db/), "
    "componentes inteligentes (agents/), jobs em scripts/ e arquivos locais em data/."
)
add_p("Componentes principais:", bold=True)
add_bullets(
    [
        "app/main.py — gateway HTTP, static, landing, atalho submit-project;",
        "app/routes_auth.py + auth.py — registro, login, token, reset;",
        "app/routes_fase_a.py — empresas, projetos, evaluate, documentos, aplicações, dashboard;",
        "agents/* — coletor, indexador, retrieval, scoring, generation, orquestrador;",
        "db/models.py — companies, employees, projects, documents, applications, edicts.",
    ]
)
add_p(
    "Divergência importante em relação ao SADS.pdf: a proposta citava React/Node/Auth.js; "
    "o PoC autentica com FastAPI + HTML/JS, e o Next.js está na landing pública."
)
add_fala(
    "Fala recomendada (arquitetura — ~45 s)",
    "“A solução foi dividida em componentes com responsabilidades específicas. "
    "O frontend atende à interação; o backend FastAPI concentra regras e integrações; "
    "o Neon mantém dados estruturados e vetores; e o motor de recomendação combina "
    "busca híbrida com pontuação explicável. Não é um monólito de chatbot: cada "
    "parte tem contrato de entrada e saída.”",
)

add_heading("6. Agentes: o coração da complexidade", 1)
add_p(
    "Usamos o termo componentes inteligentes especializados (agentes de software por tarefa). "
    "Eles não são autônomos sem controle: seguem regras, pesos e supervisão humana."
)
add_p("Duas faixas:", bold=True)
add_bullets(
    [
        "Faixa A (corpus, offline): Coletor FINEP → Indexador (embeddings) → tabela edicts.",
        "Faixa B (usuário, online): evaluate → Retrieval → Scoring → grava applications → UI.",
        "Orquestrador + Generation (template) no pipeline E2E CLI / submit-project.",
    ]
)
add_p("O que É agente × o que NÃO é:", bold=True)
add_bullets(
    [
        "AGENTE: Coletor, Indexador, Retrieval, Scoring, Generation, Orquestrador.",
        "NÃO É AGENTE: cadastro, login, upload, extração utilitária de PDF, tela do relatório, persistência CRUD.",
    ]
)
add_p("Retrieval (híbrido):", bold=True)
add_p(
    "Combina filtros SQL (órgão, sinais estruturais) com similaridade de cosseno entre "
    "o embedding do texto do projeto e o embedding dos editais (pgvector)."
)
add_p("Scoring (matriz v2):", bold=True)
add_p(
    "Pesos fixos — similaridade 30%, tema/área 25%, TRL 15%, porte 15%, região 10%, "
    "orçamento 5%. Gates penalizam prazo encerrado, porte/TRL/região incompatíveis. "
    "AHP e TOPSIS estão na proposta acadêmica, ainda não implementados no código."
)
add_p("Generation / LLM:", bold=True)
add_p(
    "No PoC, LLM_PROVIDER=none: rascunho por template local, sem envio a OpenAI/Anthropic. "
    "Não houve treinamento de modelo próprio."
)
add_fala(
    "Fala recomendada (agentes — ~55 s) — peça mais importante",
    "“A complexidade do trabalho está no pipeline de agentes. Antes do usuário, "
    "o coletor e o indexador preparam o corpus FINEP. Quando o projeto é avaliado, "
    "o Retrieval busca candidatos com filtros e similaridade semântica, e o Scoring "
    "gera um ranking com pesos explícitos e restrições. A interface apenas apresenta "
    "o resultado. Ou seja: a contribuição não é só a tela — é a orquestração de "
    "componentes especializados com saída auditável.”",
)
add_fala(
    "Fala curta se o professor perguntar ‘por que vários agentes?’",
    "“Porque cada um tem uma responsabilidade testável. O coletor não pontua projeto; "
    "o scoring não baixa edital. Essa decomposição facilita evolução, explicabilidade "
    "e controle do que toca dado sensível.”",
)

add_heading("7. Fluxo técnico da recomendação", 1)
add_p(
    "projects.raw_text + perfil da company → RetrievalAgent → lista EdictMatch → "
    "ScoringAgent → ScoreReport → registros em applications → project-evaluate.html."
)
add_p(
    "Isolamento de dados: o texto do projeto não é gravado na tabela de editais. "
    "Corpus público e projeto privado são faixas distintas."
)

add_heading("8. Segurança e privacidade (como falar sem overclaim)", 1)
add_bullets(
    [
        "Sem LLM generativo externo no fluxo atual.",
        "Projetos não são usados para treinar ou fine-tunar modelo.",
        "Projetos não entram no corpus público de editais.",
        "Uso do texto: apenas na análise (extração, similaridade, score).",
        "Multi-tenant lógico por company_id; autenticação por senha/token.",
        "Limitação: várias rotas Fase A ainda não amarram token↔empresa com Depends — roadmap de hardening.",
        "Não afirmar ‘LGPD 100%’ nem ‘vazamento impossível’.",
    ]
)
add_fala(
    "Fala recomendada (segurança — ~40 s)",
    "“O ativo sensível é o PDF do projeto. No protótipo, esse conteúdo não vai para "
    "API de LLM e não é usado para treinar modelo. Ele fica associado à organização "
    "e entra só no momento da análise, separado do corpus de editais públicos. "
    "Temos isolamento lógico multi-tenant; reforço de autorização em todas as rotas, "
    "SSO e RBAC fino são próximos passos do TCC. O sistema apoia a decisão — não "
    "substitui especialista nem garante aprovação.”",
)

add_heading("9. Implementado versus planejado", 1)
add_p("Implementado (pode demonstrar):", bold=True)
add_bullets(
    [
        "Landing, registro/login, dashboard, upload, materiais, equipe, aplicações.",
        "Coleta/indexação FINEP, retrieval, scoring v2, relatório com link FINEP.",
        "Pipeline orquestrado com generation por template.",
    ]
)
add_p("Planejado / parcial (dizer explicitamente):", bold=True)
add_bullets(
    [
        "SSO/OAuth, chat LLM com política de dados, RBAC fino.",
        "Catálogo multi-fonte (além de FINEP).",
        "AHP/TOPSIS formais.",
        "Authz completa em todas as rotas de projeto; OCR de PDF escaneado.",
    ]
)

add_heading("10. Contribuição acadêmica e próximos passos", 1)
add_p(
    "A contribuição não é apenas criar interface: é formalizar o problema de SAD em "
    "fomento, implementar pipeline coletor→índice→retrieval→scoring, oferecer ranking "
    "explicável e manter separação entre corpus público e projeto privado."
)
add_p("Próximos passos para o TCC (falar como roadmap):", bold=True)
add_bullets(
    [
        "SSO e permissões por perfil de usuário;",
        "chat assistido com LLM preferencialmente local ou com retenção zero, opt-in e só trechos;",
        "hardening de API e validação com usuários;",
        "expansão do catálogo e eventual AHP/TOPSIS após validação;",
        "documentar métricas de qualidade da recomendação.",
    ]
)
add_fala(
    "Fala recomendada (encerramento — ~25 s)",
    "“A proposta do SADS é transformar informações fragmentadas em uma recomendação "
    "estruturada, rastreável e compreensível, reduzindo o esforço inicial de análise "
    "de oportunidades de fomento — com o gestor no centro da decisão.”",
)

add_heading("11. Roteiro oral completo sugerido (~10 minutos)", 1)
add_p("Use como ensaio; ajuste ao Canva (9 slides).", italic=True, size=10)
blocos = [
    (
        "Slide 1 · Abertura (30 s)",
        "Apresentar o grupo e o SADS em uma frase: plataforma para conectar projetos aos mecanismos de fomento mais aderentes. Esta é a defesa do TC1.",
    ),
    (
        "Slide 2 · Contexto (60 s)",
        "Ecossistema brasileiro com várias instituições e mecanismos. Oportunidades existem, mas critérios e processos são distintos.",
    ),
    (
        "Slide 3 · Problema (70 s)",
        "Listar dores e a jornada Buscar→Ler→Interpretar→Comparar→Adaptar→Submeter. Decisão hoje é manual e especializada.",
    ),
    (
        "Slide 4 · Questão e objetivos (60 s)",
        "Ler a questão de pesquisa. Objetivo: SAD com ranking justificável. Três específicos. Humano decide.",
    ),
    (
        "Slide 5 · Solução (70 s)",
        "SaaS multi-tenant: perfil + PDF → motor → ranking e relatório. Benefícios: centralização, menos esforço, transparência.",
    ),
    (
        "Slide 6 · Protótipo (90 s)",
        "Mostrar jornada nas telas. Destacar o relatório. Separar o que está pronto do que é visão futura.",
    ),
    (
        "Slide 7 · Agentes (90 s)",
        "Usar a fala longa da seção 6. Mostrar Faixa A e Faixa B. Legenda agente vs não agente. Mencionar pesos e gates.",
    ),
    (
        "Slide 8 · Segurança (60 s)",
        "Usar a fala da seção 8. Três blocos: diferenciais, dados, limitações.",
    ),
    (
        "Slide 9 · Próximos passos (50 s)",
        "SSO, RBAC, chat seguro, multi-fonte, validação. Critérios de sucesso. Encerramento + obrigado.",
    ),
]
for tit, txt in blocos:
    add_p(tit, bold=True, size=11, space_after=2)
    add_p(txt, size=11, space_after=8)

add_heading("12. Perguntas frequentes (respostas de bolso)", 1)
faqs = [
    ("Foi treinado algum modelo?", "Não."),
    ("Usam ChatGPT na recomendação?", "Não no PoC. LLM_PROVIDER=none; template local."),
    ("Por que não só um chatbot?", "Porque precisamos de gates, ranking e justificativa auditável."),
    ("AHP e TOPSIS estão prontos?", "Estão na proposta; o código usa matriz de pesos fixos v2."),
    ("O sistema cobre todo o Brasil?", "O piloto é FINEP; multi-fonte é próximo passo."),
    ("Substitui consultoria?", "Não. Apoia a triagem inicial."),
    ("Como o multi-tenant funciona?", "Dados ligados a company_id; cada org vê o seu."),
    ("O que falta de segurança?", "Reforçar autorização server-side, SSO e RBAC fino no TCC."),
]
for q, a in faqs:
    add_p("P: " + q, bold=True, size=11, space_after=1)
    add_p("R: " + a, size=11, space_after=8)

add_heading("13. Checklist individual (antes de dormir)", 1)
add_bullets(
    [
        "Sei desenhar o fluxo do usuário e a faixa do corpus.",
        "Sei dizer o que é agente e o que não é.",
        "Sei os pesos do scoring e que AHP/TOPSIS são futuros.",
        "Sei explicar segurança sem overclaim.",
        "Sei o que está implementado vs planejado.",
        "Ensaiei minha fala em voz alta pelo menos duas vezes.",
        "Sei o plano B se a demo falhar (prints + diagrama).",
    ]
)

add_heading("14. Referências internas", 1)
add_bullets(
    [
        "docs/MANUAL_COMPLETO_SADS.md — manual completo",
        "docs/ARQUITETURA_SADS.md — diagramas e componentes",
        "docs/RESUMO_GRUPO_SADS.md — versão ultra-curta",
        "docs/ROTEIRO_APRESENTACAO_TC1.md — tempos por slide",
        "docs/PERGUNTAS_E_RESPOSTAS_TC1.md — Q&A expandido",
        "docs/GUIA_DEMONSTRACAO.md — demo ao vivo",
        "docs/TCC/apresentacao_tc1/SADS_TC1_CANVA.md — conteúdo Canva",
        "docs/TCC/apresentacao_tc1/DIAGRAMA_AGENTES.md — agentes detalhados",
    ]
)

foot = doc.add_paragraph()
foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = foot.add_run("\n— Fim do guia intermediário SADS / TC1 —")
set_run_font(r, size=10, color=RGBColor(0x66, 0x66, 0x66))

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("Wrote", OUT, "bytes", OUT.stat().st_size)
