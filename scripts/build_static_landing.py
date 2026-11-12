"""Gera a landing SADS em um único HTML (CSS + logo embutidos) para GitHub Pages / offline."""

from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "web" / "assets" / "sads-logo.png"
OUT = ROOT / "docs" / "sads.html"
INDEX = ROOT / "docs" / "index.html"
README = ROOT / "docs" / "README.md"


def main() -> None:
    logo_b64 = base64.b64encode(LOGO.read_bytes()).decode("ascii")
    logo_uri = f"data:image/png;base64,{logo_b64}"
    year = 2026

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SADS — Sistema de Apoio à Decisão para Fomento à Inovação</title>
  <meta name="description" content="Analise projetos com IA, receba ranking explicável de programas de fomento, lacunas e plano de ação. FINEP, EMBRAPII, FAPESP, BNDES e mais." />
  <link rel="icon" href="{logo_uri}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet" />
  <style>
{CSS}
  </style>
</head>
<body>
  <header class="site-header">
    <div class="shell header-inner">
      <a class="brand" href="#topo" aria-label="SADS — página inicial">
        <img src="{logo_uri}" alt="" width="80" height="80" />
        <span>SADS</span>
      </a>
      <nav class="nav-desktop" aria-label="Principal">
        <a href="#produto">Produto</a>
        <a href="#como-funciona">Como funciona</a>
        <a href="#recursos">Recursos</a>
        <a href="#publico">Público-alvo</a>
        <a href="#demonstracao">Demonstração</a>
      </nav>
      <div class="header-cta">
        <a class="btn ghost" href="#entrar">Login</a>
        <a class="btn primary" href="#criar-conta">Analisar Projeto</a>
      </div>
      <button type="button" class="menu-btn" id="menu-btn" aria-expanded="false" aria-controls="mobile-nav">
        <span class="sr-only">Abrir menu</span>
        <span id="menu-icon" aria-hidden="true">☰</span>
      </button>
    </div>
    <div id="mobile-nav" class="mobile-nav" hidden>
      <nav class="shell mobile-nav-inner" aria-label="Mobile">
        <a href="#produto">Produto</a>
        <a href="#como-funciona">Como funciona</a>
        <a href="#recursos">Recursos</a>
        <a href="#publico">Público-alvo</a>
        <a href="#demonstracao">Demonstração</a>
        <div class="mobile-cta">
          <a class="btn secondary" href="#entrar">Login</a>
          <a class="btn primary" href="#criar-conta">Analisar Projeto</a>
        </div>
      </nav>
    </div>
  </header>

  <main id="topo">
    <!-- Hero -->
    <section id="produto" class="hero">
      <div class="hero-glow" aria-hidden="true"></div>
      <div class="shell hero-grid">
        <div>
          <p class="eyebrow">Sistema de Apoio à Decisão</p>
          <h1>Descubra os melhores programas de fomento para o seu projeto — com clareza sobre o porquê.</h1>
          <p class="lead">
            O SADS analisa o PDF do projeto e o perfil da organização, cruza critérios de
            elegibilidade e entrega um ranking explicável de programas — com lacunas e plano de ação
            para submissão.
          </p>
          <div class="btn-row">
            <a class="btn primary lg" href="#criar-conta">Analisar meu projeto</a>
            <a class="btn secondary lg" href="#demonstracao">Ver demonstração</a>
          </div>
          <dl class="hero-stats">
            <div><dt>Minutos</dt><dd>em vez de semanas</dd></div>
            <div><dt>Explicável</dt><dd>score por critério</dd></div>
            <div><dt>Multi-fonte</dt><dd>FINEP e mais</dd></div>
          </dl>
        </div>
        <div class="hero-aside">
          {report_mockup(compact=True)}
        </div>
      </div>
    </section>

    <!-- Problem -->
    <section id="problema" class="section muted">
      <div class="shell">
        <div class="section-head">
          <p class="eyebrow">O problema</p>
          <h2>Encontrar fomento certo ainda é lento, fragmentado e opaco</h2>
          <p class="section-lead">Gestores de inovação enfrentam volume de editais, regras distintas de elegibilidade e pouca evidência para decidir onde investir esforço de submissão.</p>
        </div>
        <div class="grid-4">
          {card_stat("Dezenas", "de fontes dispersas", "Editais e programas espalhados entre FINEP, EMBRAPII, FAPs, BNDES e incentivos fiscais.")}
          {card_stat("Semanas", "em triagem manual", "Equipes de P&amp;D gastam tempo lendo chamadas sem saber se o projeto é elegível de fato.")}
          {card_stat("Alto", "custo de consultoria", "Apoio especializado ajuda, mas não escala para múltiplos projetos e reavaliações.")}
          {card_stat("Baixa", "explicabilidade", "Mesmo quando há uma indicação, falta clareza sobre critérios, gaps e próximo passo.")}
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section id="como-funciona" class="section">
      <div class="shell">
        <div class="section-head">
          <p class="eyebrow">Como funciona</p>
          <h2>Do PDF ao ranking em quatro etapas</h2>
          <p class="section-lead">Fluxo pensado para áreas de inovação: rápido de operar, auditável e pronto para discussão com diretoria ou banca interna.</p>
        </div>
        <ol class="grid-4 steps">
          {step("01", "Cadastre a organização", "Informe CNPJ, porte, área de atuação e dados institucionais. O perfil alimenta a elegibilidade.")}
          {step("02", "Envie o PDF do projeto", "Faça upload da proposta. O SADS extrai escopo, maturidade tecnológica e sinais de alinhamento.")}
          {step("03", "Receba a análise automática", "Ranking de programas, score por critério, lacunas e justificativas — em minutos, não em semanas.")}
          {step("04", "Planeje a submissão", "Use o plano de ação para priorizar ajustes documentais e aumentar a competitividade da proposta.")}
        </ol>
      </div>
    </section>

    <!-- What you get -->
    <section id="recursos" class="section muted">
      <div class="shell">
        <div class="section-head">
          <p class="eyebrow">O que você recebe</p>
          <h2>Um dossiê de decisão — não apenas uma lista de editais</h2>
          <p class="section-lead">Cada análise entrega artefatos que a equipe pode usar em comitês internos, com rastreabilidade do raciocínio.</p>
        </div>
        <div class="grid-4">
          {feature("Ranking de programas", "Ordem objetiva de aderência entre o projeto e chamadas disponíveis.")}
          {feature("Score explicável", "Pontuação decomponível por critério — não uma caixa-preta.")}
          {feature("Critérios atendidos", "Visão clara do que já está alinhado à elegibilidade e ao escopo.")}
          {feature("Critérios faltantes", "Identificação do que ainda bloqueia ou enfraquece a candidatura.")}
          {feature("Lacunas do projeto", "Gaps documentais e de conteúdo priorizados por impacto.")}
          {feature("Plano de ação", "Sequência sugerida para reforçar a proposta antes da submissão.")}
          {feature("Histórico de análises", "Reavaliações e comparações ao longo do ciclo do projeto.")}
          {feature("Recomendação com IA", "Cruzamento semântico do texto do projeto com o corpus de editais.")}
        </div>
      </div>
    </section>

    <!-- Comparison -->
    <section id="diferenciais" class="section">
      <div class="shell">
        <div class="section-head">
          <p class="eyebrow">Diferenciais</p>
          <h2>SADS frente à busca manual e às consultorias</h2>
          <p class="section-lead">Não substitui julgamento humano nem banca oficial. Acelera a triagem, padroniza a evidência e reduz o custo de explorar opções.</p>
        </div>
        <div class="table-wrap">
          <table>
            <caption class="sr-only">Comparativo entre SADS, busca manual e consultorias</caption>
            <thead>
              <tr>
                <th scope="col">Critério</th>
                <th scope="col">SADS</th>
                <th scope="col">Busca manual</th>
                <th scope="col">Consultorias</th>
              </tr>
            </thead>
            <tbody>
              <tr><th scope="row">Tempo para triagem</th><td class="hl">Minutos</td><td>Dias a semanas</td><td>Dias, sob demanda</td></tr>
              <tr><th scope="row">Custo marginal por projeto</th><td class="hl">Baixo e previsível</td><td>Alto (horas internas)</td><td>Alto (honorários)</td></tr>
              <tr><th scope="row">Escalabilidade</th><td class="hl">Vários projetos em paralelo</td><td>Limitada pela equipe</td><td>Limitada por contrato</td></tr>
              <tr><th scope="row">Explicabilidade</th><td class="hl">Score por critério + lacunas</td><td>Depende do analista</td><td>Depende do consultor</td></tr>
              <tr><th scope="row">LGPD e trilha</th><td class="hl">Controles multi-tenant</td><td>Variável</td><td>Variável</td></tr>
              <tr><th scope="row">Centralização</th><td class="hl">Histórico único na plataforma</td><td>Planilhas e e-mails</td><td>Relatórios pontuais</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Demo -->
    <section id="demonstracao" class="section muted">
      <div class="shell">
        <div class="section-head">
          <p class="eyebrow">Demonstração</p>
          <h2>Veja o valor do relatório antes de criar conta</h2>
          <p class="section-lead">Exemplo ilustrativo do que a equipe recebe após o upload: ranking, score, lacunas e encaminhamentos.</p>
        </div>
        <div class="demo-grid">
          <div class="demo-side">
            <article class="card">
              <p class="mini-label">Projeto enviado</p>
              <p class="card-title">Desenvolvimento de sensores IoT para agricultura de precisão</p>
              <p class="muted">PDF · 18 páginas · TRL 4–5 · Empresa EPP</p>
            </article>
            <div class="dashed-box">
              <p class="muted">A análise cruza o texto do projeto com o corpus indexado (FINEP e demais fontes configuradas), avalia elegibilidade e devolve um dossiê navegável — útil para priorizar onde vale a pena escrever a proposta completa.</p>
              <ol>
                <li>1. Ranking ordenado por aderência</li>
                <li>2. Explicação do score por critério</li>
                <li>3. Lacunas e plano de ação</li>
              </ol>
            </div>
          </div>
          {report_mockup(compact=False, large=True)}
        </div>
      </div>
    </section>

    <!-- Audience -->
    <section id="publico" class="section">
      <div class="shell">
        <div class="section-head">
          <p class="eyebrow">Público-alvo</p>
          <h2>Feito para quem decide onde investir esforço de captação</h2>
          <p class="section-lead">Do empreendedor à diretoria de inovação: o SADS fala a linguagem de elegibilidade, prazo e competitividade.</p>
        </div>
        <div class="grid-3">
          {audience("Startups", "Identifique chamadas compatíveis com estágio, porte e tema — sem dispersar o time em triagem interminável.")}
          {audience("Empresas e P&amp;D", "Padronize a avaliação de pipeline de inovação e compartilhe evidências com liderança e compliance.")}
          {audience("ICTs e centros de pesquisa", "Acelere o matching entre projetos de P&amp;D e instrumentos de fomento públicos e parcerias.")}
          {audience("Consultorias", "Escale a pré-análise de clientes com ranking explicável e histórico por organização.")}
          {audience("Universidades", "Apoie NITs e escritórios de projetos na priorização de submissões e na preparação documental.")}
        </div>
        <p class="footnote">Fontes suportadas na plataforma incluem FINEP, EMBRAPII, FAPESP, BNDES, incentivos fiscais e outros programas de inovação — conforme corpus indexado.</p>
      </div>
    </section>

    <!-- Security -->
    <section id="seguranca" class="section dark">
      <div class="shell">
        <div class="section-head">
          <p class="eyebrow soft">Segurança e conformidade</p>
          <h2>Construído para ambientes em que confiança é requisito</h2>
          <p class="section-lead soft">Empresas, ICTs e universidades precisam de trilha clara sobre quem acessa o quê — e por quê.</p>
        </div>
        <div class="grid-4">
          {security("Multi-tenant", "Isolamento lógico por organização. Dados de uma empresa não se misturam com os de outra.")}
          {security("Controle de acesso (RBAC)", "Perfis e permissões para separar quem cadastra, quem analisa e quem apenas consulta.")}
          {security("Autenticação corporativa", "Roadmap com OAuth/SSO para integrar identidade institucional na Fase B.")}
          {security("LGPD", "Tratamento alinhado a finalidade, minimização e direitos do titular — com política publicada.")}
        </div>
      </div>
    </section>

    <!-- Final CTA -->
    <section class="final-cta">
      <div class="shell center">
        <p class="eyebrow">Comece agora</p>
        <h2>Pronto para descobrir os melhores programas para o seu projeto?</h2>
        <p class="section-lead center-lead">Cadastre a organização, envie o PDF e receba um ranking explicável com lacunas e plano de ação.</p>
        <div class="btn-row center-row">
          <a class="btn primary lg" href="#criar-conta">Analisar Projeto</a>
          <a class="btn secondary lg" href="#criar-conta">Criar Conta</a>
        </div>
      </div>
    </section>

    <!-- Static auth panels (demo) -->
    <section id="entrar" class="section muted">
      <div class="shell narrow">
        <div class="section-head">
          <p class="eyebrow">Acesso</p>
          <h2>Entrar no SADS</h2>
          <p class="section-lead">Versão estática para apresentação / GitHub. No servidor completo, o login autentica contra a API.</p>
        </div>
        <form class="card form-card" id="login-form">
          <label>Nome da empresa *</label>
          <input name="company_name" required placeholder="Razão social ou nome fantasia" />
          <label>E-mail corporativo *</label>
          <input name="email" type="email" required />
          <label>Senha *</label>
          <input name="password" type="password" required minlength="8" />
          <button class="btn primary" type="submit">Entrar</button>
          <p class="muted form-note">Ainda não tem conta? <a href="#criar-conta">Criar conta da organização</a></p>
          <p class="form-msg" id="login-msg" hidden></p>
        </form>
      </div>
    </section>

    <section id="criar-conta" class="section">
      <div class="shell narrow">
        <div class="section-head">
          <p class="eyebrow">Onboarding</p>
          <h2>Criar conta da organização</h2>
          <p class="section-lead">Nesta página estática o formulário é ilustrativo. Para análise real de PDF, use a aplicação com API.</p>
        </div>
        <form class="card form-card" id="register-form">
          <h3>Empresa</h3>
          <label>Razão social / nome *</label>
          <input name="company_name" required />
          <div class="row-2">
            <div>
              <label>Porte</label>
              <select name="size"><option value="">—</option><option>MEI</option><option>ME</option><option>EPP</option><option>Demais</option></select>
            </div>
            <div>
              <label>UF</label>
              <input name="uf" maxlength="2" />
            </div>
          </div>
          <h3>Administrador</h3>
          <label>Seu nome *</label>
          <input name="admin_name" required />
          <label>E-mail corporativo *</label>
          <input name="admin_email" type="email" required />
          <label>Senha * (mín. 8)</label>
          <input name="password" type="password" required minlength="8" />
          <button class="btn primary" type="submit">Criar conta</button>
          <p class="muted form-note">Já possui conta? <a href="#entrar">Fazer login</a></p>
          <p class="form-msg" id="register-msg" hidden></p>
        </form>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="shell footer-grid">
      <div>
        <div class="brand footer-brand">
          <img src="{logo_uri}" alt="" width="88" height="88" />
          <span>SADS</span>
        </div>
        <p class="footer-about">Sistema de Apoio à Decisão para Fomento à Inovação — análise de projetos e recomendação explicável de programas.</p>
      </div>
      <div>
        <p class="footer-col">Produto</p>
        <ul>
          <li><a href="#produto">Visão geral</a></li>
          <li><a href="#como-funciona">Como funciona</a></li>
          <li><a href="#demonstracao">Demonstração</a></li>
          <li><a href="demo/sads-relatorio-guardrail.html">Demo relatório (guardrail)</a></li>
        </ul>
      </div>
      <div>
        <p class="footer-col">Institucional</p>
        <ul>
          <li><a href="#publico">Público-alvo</a></li>
          <li><a href="#seguranca">Segurança e LGPD</a></li>
          <li><a href="#entrar">Acessar painel</a></li>
        </ul>
      </div>
      <div>
        <p class="footer-col">Legal</p>
        <ul>
          <li><a href="#seguranca">Política de Privacidade</a></li>
          <li><a href="#seguranca">LGPD</a></li>
          <li><a href="mailto:contato@sads.local">Contato</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="shell footer-bottom-inner">
        <p>© {year} SADS. Uso acadêmico / protótipo TCC.</p>
        <p>Scores são heurísticos e não substituem leitura integral do edital.</p>
      </div>
    </div>
  </footer>

  <script>
    (function () {{
      const btn = document.getElementById("menu-btn");
      const panel = document.getElementById("mobile-nav");
      const icon = document.getElementById("menu-icon");
      btn.addEventListener("click", () => {{
        const open = panel.hasAttribute("hidden");
        if (open) panel.removeAttribute("hidden");
        else panel.setAttribute("hidden", "");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        icon.textContent = open ? "×" : "☰";
      }});
      panel.querySelectorAll("a").forEach((a) => {{
        a.addEventListener("click", () => {{
          panel.setAttribute("hidden", "");
          btn.setAttribute("aria-expanded", "false");
          icon.textContent = "☰";
        }});
      }});

      function demoSubmit(formId, msgId) {{
        const form = document.getElementById(formId);
        const msg = document.getElementById(msgId);
        form.addEventListener("submit", (ev) => {{
          ev.preventDefault();
          msg.hidden = false;
          msg.textContent =
            "Esta é a landing estática (arquivo único). Para login e análise reais, rode o servidor SADS.";
        }});
      }}
      demoSubmit("login-form", "login-msg");
      demoSubmit("register-form", "register-msg");
    }})();
  </script>
</body>
</html>
"""

    OUT.write_text(html, encoding="utf-8")
    INDEX.write_text(
        f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0; url=sads.html" />
  <title>SADS</title>
  <link rel="canonical" href="sads.html" />
  <link rel="icon" href="{logo_uri}" />
</head>
<body>
  <p><a href="sads.html">Abrir página SADS</a></p>
</body>
</html>
""",
        encoding="utf-8",
    )
    README.write_text(
        """# Docs públicos (GitHub Pages)

## Página SADS (landing completa)

Arquivo único, abre em qualquer navegador:

- [`sads.html`](sads.html) — landing completa (produto, como funciona, demo, segurança, login/cadastro ilustrativos)
- [`index.html`](index.html) — redireciona para `sads.html`

### Abrir localmente

Duplo clique em `docs/sads.html`.

### GitHub Pages

1. Settings → Pages → Deploy from a branch → pasta `/docs`
2. URL: `https://<usuario>.github.io/<repositorio>/` ou `.../sads.html`

### Extra

- [`demo/sads-relatorio-guardrail.html`](demo/sads-relatorio-guardrail.html) — mock do relatório com guardrail (sem %)
""",
        encoding="utf-8",
    )
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"Wrote {INDEX}")
    print(f"Wrote {README}")


def card_stat(stat: str, label: str, text: str) -> str:
    return f"""<article class="card">
            <p class="stat">{stat}</p>
            <p class="stat-label">{label}</p>
            <p class="muted">{text}</p>
          </article>"""


def step(n: str, title: str, text: str) -> str:
    return f"""<li class="card">
            <span class="step-n">{n}</span>
            <h3>{title}</h3>
            <p class="muted">{text}</p>
          </li>"""


def feature(title: str, text: str) -> str:
    return f"""<article class="card">
            <div class="accent-bar" aria-hidden="true"></div>
            <h3>{title}</h3>
            <p class="muted">{text}</p>
          </article>"""


def audience(title: str, text: str) -> str:
    return f"""<article class="card pad-lg">
            <h3>{title}</h3>
            <p class="muted">{text}</p>
          </article>"""


def security(title: str, text: str) -> str:
    return f"""<article class="card dark-card">
            <h3>{title}</h3>
            <p>{text}</p>
          </article>"""


def report_mockup(*, compact: bool = False, large: bool = False) -> str:
    gaps = ""
    if not compact:
        gaps = """
          <ul class="mock-list">
            <li><span class="dot cyan"></span>Escopo alinhado a inovação tecnológica</li>
            <li><span class="dot cyan"></span>Documentação mínima parcialmente atendida</li>
            <li><span class="dot amber"></span>Lacuna: detalhar contrapartida financeira</li>
          </ul>"""
    grid = "mock-body large" if large else "mock-body"
    return f"""
        <aside class="mock {"shadow-panel" if large else ""}" aria-label="Prévia do relatório SADS">
          <div class="mock-head">
            <div>
              <p class="mock-kicker">Relatório de recomendação</p>
              <p class="mock-title">Projeto Semicondutores Avançados</p>
            </div>
            <div class="mock-badge">Análise concluída</div>
          </div>
          <div class="{grid}">
            <div>
              <p class="mini-label">Melhor oportunidade</p>
              <h3 class="mock-program">Subvenção Econômica — FINEP</h3>
              <p class="muted">Alta aderência temática, porte elegível e TRL compatível com a chamada vigente.</p>
              {gaps}
            </div>
            <div class="mock-score">
              <p class="mini-label">Compatibilidade</p>
              <p class="score-big">92%</p>
              <p class="score-hint">Alta chance relativa</p>
              <div class="bar"><span style="width:92%"></span></div>
            </div>
          </div>
          <div class="mock-rank">
            <p class="mini-label">Ranking de programas</p>
            <ol>
              <li><span class="medal">1</span><span class="name">Subvenção Econômica — FINEP</span><span class="pct high">92%</span></li>
              <li><span class="medal">2</span><span class="name">EMBRAPII</span><span class="pct high">85%</span></li>
              <li><span class="medal">3</span><span class="name">PRONINC</span><span class="pct mid">78%</span></li>
            </ol>
          </div>
        </aside>"""


CSS = r"""
:root {
  --navy-950: #04071f;
  --navy-900: #070b2e;
  --navy-800: #0c1238;
  --cyan: #2ec7ff;
  --cyan-soft: #5ad6ff;
  --ink: #0b1220;
  --ink-soft: #3d4b66;
  --ink-faint: #6b7a96;
  --paper: #f7f8fb;
  --paper-card: #ffffff;
  --paper-line: #e6eaf2;
  --shadow-soft: 0 1px 2px rgba(7, 11, 46, 0.04), 0 12px 32px rgba(7, 11, 46, 0.06);
  --shadow-panel: 0 24px 60px rgba(7, 11, 46, 0.12);
  --font-sans: "Inter", system-ui, sans-serif;
  --font-display: "Montserrat", system-ui, sans-serif;
  --focus: #2ec7ff;
  --content: 1120px;
}
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--font-sans);
  background: var(--paper);
  color: var(--ink);
  antialiased: true;
  -webkit-font-smoothing: antialiased;
}
::selection { background: rgba(46, 199, 255, 0.25); }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 3px; }
a { color: inherit; text-decoration: none; }
img { display: block; max-width: 100%; height: auto; }
ul, ol { margin: 0; padding: 0; list-style: none; }
h1, h2, h3 { margin: 0; font-family: var(--font-display); }
p { margin: 0; }
.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0;
}
.shell {
  width: 100%;
  max-width: var(--content);
  margin: 0 auto;
  padding: 0 1.25rem;
}
@media (min-width: 640px) { .shell { padding: 0 1.5rem; } }
@media (min-width: 1024px) { .shell { padding: 0 2rem; } }

.eyebrow {
  font-family: var(--font-display);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--cyan);
}
.eyebrow.soft { color: var(--cyan-soft); }

.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid rgba(230, 234, 242, 0.8);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  height: 4rem;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.brand img { height: 2.5rem; width: auto; }
.brand span {
  display: none;
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--navy-900);
}
@media (min-width: 640px) { .brand span { display: inline; } }
.nav-desktop { display: none; align-items: center; gap: 1.5rem; }
.nav-desktop a {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--ink-soft);
}
.nav-desktop a:hover { color: var(--navy-900); }
@media (min-width: 1024px) { .nav-desktop { display: flex; } }
.header-cta { display: none; align-items: center; gap: 0.5rem; }
@media (min-width: 640px) { .header-cta { display: flex; } }
.menu-btn {
  display: inline-flex;
  height: 2.5rem;
  width: 2.5rem;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  border: 1px solid var(--paper-line);
  background: #fff;
  cursor: pointer;
  font-size: 1.125rem;
}
@media (min-width: 1024px) { .menu-btn { display: none; } }
.mobile-nav {
  border-top: 1px solid var(--paper-line);
  background: #fff;
}
.mobile-nav-inner { display: flex; flex-direction: column; gap: 0.25rem; padding-top: 0.75rem; padding-bottom: 0.75rem; }
.mobile-nav a {
  border-radius: 0.5rem;
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--ink-soft);
}
.mobile-nav a:hover { background: var(--paper); }
.mobile-cta {
  margin-top: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border-top: 1px solid var(--paper-line);
  padding-top: 0.75rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  padding: 0.625rem 1rem;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  font-family: inherit;
}
.btn.lg { padding: 0.75rem 1.25rem; }
@media (min-width: 640px) { .btn.lg { font-size: 1rem; } }
.btn.primary {
  background: var(--navy-900);
  color: #fff;
  box-shadow: var(--shadow-soft);
}
.btn.primary:hover { background: var(--navy-800); }
.btn.secondary {
  background: #fff;
  color: var(--navy-900);
  border-color: var(--paper-line);
}
.btn.secondary:hover { background: var(--paper); }
.btn.ghost {
  background: transparent;
  color: var(--navy-900);
}
.btn.ghost:hover { background: rgba(255,255,255,0.6); }

.hero {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--paper-line);
  background: #fff;
}
.hero-glow {
  pointer-events: none;
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at top right, rgba(46,199,255,0.08), transparent 45%);
}
.hero-grid {
  position: relative;
  display: grid;
  gap: 3rem;
  padding: 4rem 1.25rem;
  align-items: center;
}
@media (min-width: 640px) {
  .hero-grid { padding-left: 1.5rem; padding-right: 1.5rem; }
}
@media (min-width: 1024px) {
  .hero-grid {
    grid-template-columns: 1.05fr 0.95fr;
    padding: 6rem 2rem;
  }
}
.hero h1 {
  margin-top: 1rem;
  font-size: 2.25rem;
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.02em;
  color: var(--navy-900);
}
@media (min-width: 640px) { .hero h1 { font-size: 3rem; } }
@media (min-width: 1024px) { .hero h1 { font-size: 3.25rem; } }
.lead {
  margin-top: 1.25rem;
  max-width: 36rem;
  font-size: 1rem;
  line-height: 1.65;
  color: var(--ink-soft);
}
@media (min-width: 640px) { .lead { font-size: 1.125rem; } }
.btn-row { margin-top: 2rem; display: flex; flex-wrap: wrap; gap: 0.75rem; }
.hero-stats {
  margin: 2.5rem 0 0;
  max-width: 32rem;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  border-top: 1px solid var(--paper-line);
  padding-top: 2rem;
}
.hero-stats dt {
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--navy-900);
}
.hero-stats dd { margin: 0.25rem 0 0; font-size: 0.75rem; color: var(--ink-faint); }
@media (min-width: 1024px) { .hero-aside { padding-left: 1rem; } }

.section { padding: 5rem 0; background: #fff; }
.section.muted { background: var(--paper); }
.section.dark { background: var(--navy-900); color: #fff; }
@media (min-width: 640px) { .section { padding: 6rem 0; } }
.section-head { max-width: 48rem; }
.section-head h2 {
  margin-top: 0.75rem;
  font-size: 1.875rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--navy-900);
}
@media (min-width: 640px) { .section-head h2 { font-size: 2.25rem; } }
.section.dark .section-head h2 { color: #fff; }
.section-lead {
  margin-top: 0.75rem;
  max-width: 42rem;
  font-size: 1rem;
  line-height: 1.65;
  color: var(--ink-soft);
}
@media (min-width: 640px) { .section-lead { font-size: 1.125rem; } }
.section-lead.soft, .section.dark .section-lead { color: rgba(255,255,255,0.7); }
.section-head + .grid-4,
.section-head + .grid-3,
.section-head + .steps,
.section-head + .table-wrap,
.section-head + .demo-grid { margin-top: 3rem; }

.card {
  border-radius: 1rem;
  border: 1px solid var(--paper-line);
  background: var(--paper-card);
  box-shadow: var(--shadow-soft);
  padding: 1.25rem;
}
.card.pad-lg { padding: 1.5rem; }
.card h3 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--navy-900);
}
.card.pad-lg h3 { font-size: 1.125rem; }
.muted { margin-top: 0.5rem; font-size: 0.875rem; line-height: 1.6; color: var(--ink-soft); }
.stat {
  font-family: var(--font-display);
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--navy-900);
}
.stat-label { margin-top: 0.25rem; font-size: 0.875rem; font-weight: 600; color: var(--cyan); }
.accent-bar {
  margin-bottom: 1rem;
  height: 0.25rem;
  width: 2rem;
  border-radius: 999px;
  background: var(--cyan);
}
.step-n {
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--cyan);
}
.steps h3 { margin-top: 0.75rem; font-size: 1.125rem; }
.steps .muted { margin-top: 0.5rem; }

.grid-4 {
  display: grid;
  gap: 1rem;
}
@media (min-width: 640px) { .grid-4 { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .grid-4 { grid-template-columns: repeat(4, 1fr); } }
.grid-3 {
  display: grid;
  gap: 1rem;
}
@media (min-width: 640px) { .grid-3 { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .grid-3 { grid-template-columns: repeat(3, 1fr); } }

.table-wrap {
  overflow-x: auto;
  border-radius: 1rem;
  border: 1px solid var(--paper-line);
  background: #fff;
  box-shadow: var(--shadow-soft);
}
table {
  min-width: 720px;
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.875rem;
}
thead tr { border-bottom: 1px solid var(--paper-line); background: var(--paper); }
th, td { padding: 0.875rem 1rem; }
thead th { font-weight: 600; color: var(--ink-faint); }
thead th:nth-child(2) { color: var(--navy-900); }
thead th:nth-child(n+3) { color: var(--ink-soft); }
tbody tr { border-bottom: 1px solid var(--paper-line); }
tbody tr:last-child { border-bottom: 0; }
tbody th { font-weight: 500; color: var(--navy-900); }
td { color: var(--ink-soft); }
td.hl { font-weight: 500; color: var(--navy-900); }

.demo-grid {
  display: grid;
  gap: 2rem;
  align-items: start;
}
@media (min-width: 1024px) {
  .demo-grid { grid-template-columns: 0.85fr 1.15fr; }
}
.demo-side { display: flex; flex-direction: column; gap: 1.25rem; }
.mini-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--ink-faint);
}
.card-title {
  margin-top: 0.5rem;
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--navy-900);
}
.dashed-box {
  border-radius: 1rem;
  border: 1px dashed var(--paper-line);
  background: #fff;
  padding: 1.25rem;
}
.dashed-box ol { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.dashed-box li { font-size: 0.875rem; color: var(--navy-900); }
.footnote {
  margin-top: 2rem;
  font-size: 0.875rem;
  color: var(--ink-faint);
}

.dark-card {
  border-radius: 1rem;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(4px);
  padding: 1.25rem;
}
.dark-card h3 { color: #fff; font-size: 1rem; }
.dark-card p { margin-top: 0.5rem; font-size: 0.875rem; line-height: 1.6; color: rgba(255,255,255,0.7); }

.final-cta {
  border-top: 1px solid var(--paper-line);
  border-bottom: 1px solid var(--paper-line);
  background: var(--paper);
  padding: 5rem 0;
}
@media (min-width: 640px) { .final-cta { padding: 6rem 0; } }
.center { text-align: center; max-width: 48rem; }
.center .eyebrow { display: inline-block; }
.center h2 {
  margin-top: 0.75rem;
  font-size: 1.875rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--navy-900);
}
@media (min-width: 640px) { .center h2 { font-size: 2.25rem; } }
.center-lead { margin-left: auto; margin-right: auto; }
.center-row { justify-content: center; }

.narrow { max-width: 40rem; }
.form-card { display: flex; flex-direction: column; gap: 0.35rem; }
.form-card h3 {
  margin: 0.75rem 0 0.25rem;
  font-size: 1.05rem;
  color: var(--navy-900);
}
.form-card label {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--ink-soft);
}
.form-card input,
.form-card select {
  width: 100%;
  border: 1px solid var(--paper-line);
  border-radius: 0.5rem;
  padding: 0.65rem 0.75rem;
  font: inherit;
  background: #fff;
}
.form-card .btn { margin-top: 1rem; }
.form-note { margin-top: 1rem; }
.form-note a { color: var(--navy-900); text-decoration: underline; }
.form-msg {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: rgba(46, 199, 255, 0.12);
  color: var(--navy-900);
  font-size: 0.875rem;
}
.row-2 {
  display: grid;
  gap: 0.75rem;
}
@media (min-width: 640px) { .row-2 { grid-template-columns: 1fr 1fr; } }

.mock {
  border-radius: 1rem;
  border: 1px solid var(--paper-line);
  background: #fff;
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}
.mock.shadow-panel { box-shadow: var(--shadow-panel); }
.mock-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  background: var(--navy-900);
  color: #fff;
  padding: 0.75rem 1rem;
}
.mock-kicker {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--cyan-soft);
}
.mock-title { margin-top: 0.15rem; font-size: 0.875rem; font-weight: 600; }
.mock-badge {
  border-radius: 999px;
  background: rgba(255,255,255,0.1);
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--cyan-soft);
  white-space: nowrap;
}
.mock-body { display: grid; gap: 1rem; padding: 1rem; }
@media (min-width: 640px) {
  .mock-body { padding: 1.25rem; }
  .mock-body.large { grid-template-columns: 1.2fr 0.8fr; }
}
.mock-program {
  margin-top: 0.25rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--navy-900);
}
.mock-list { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.mock-list li {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--ink-soft);
}
.dot {
  margin-top: 0.4rem;
  height: 0.375rem;
  width: 0.375rem;
  border-radius: 999px;
  flex-shrink: 0;
}
.dot.cyan { background: var(--cyan); }
.dot.amber { background: #f59e0b; }
.mock-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
  border: 1px solid var(--paper-line);
  background: var(--paper);
  padding: 1.25rem 1rem;
  text-align: center;
}
.score-big {
  margin-top: 0.5rem;
  font-family: var(--font-display);
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--navy-900);
}
.score-hint { margin-top: 0.25rem; font-size: 0.75rem; font-weight: 500; color: #047857; }
.bar {
  margin-top: 1rem;
  height: 0.5rem;
  width: 100%;
  overflow: hidden;
  border-radius: 999px;
  background: #fff;
}
.bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--navy-900);
}
.mock-rank {
  border-top: 1px solid var(--paper-line);
  padding: 1rem;
}
@media (min-width: 640px) { .mock-rank { padding: 1rem 1.25rem 1.25rem; } }
.mock-rank .mini-label { margin-bottom: 0.75rem; }
.mock-rank ol { display: flex; flex-direction: column; gap: 0.5rem; }
.mock-rank li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  border-radius: 0.75rem;
  border: 1px solid var(--paper-line);
  background: #fff;
  padding: 0.625rem 0.75rem;
}
.medal {
  display: inline-flex;
  height: 1.75rem;
  width: 1.75rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  background: var(--navy-900);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  margin-right: 0.75rem;
}
.mock-rank .name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--navy-900);
}
.mock-rank li { display: flex; }
.mock-rank li > .medal + .name { /* keep */ }
.pct { flex-shrink: 0; font-size: 0.875rem; font-weight: 700; }
.pct.high { color: #047857; }
.pct.mid { color: #b45309; }
.mock-rank li {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
}
.mock-rank .medal { margin-right: 0; }

.site-footer { background: var(--navy-950); color: #fff; }
.footer-grid {
  display: grid;
  gap: 2.5rem;
  padding: 3.5rem 1.25rem;
}
@media (min-width: 640px) {
  .footer-grid { grid-template-columns: repeat(2, 1fr); padding-left: 1.5rem; padding-right: 1.5rem; }
}
@media (min-width: 1024px) {
  .footer-grid { grid-template-columns: repeat(4, 1fr); padding-left: 2rem; padding-right: 2rem; }
}
.footer-brand img { height: 2.75rem; width: auto; }
.footer-about {
  margin-top: 1rem;
  max-width: 20rem;
  font-size: 0.875rem;
  line-height: 1.6;
  color: rgba(255,255,255,0.65);
}
.footer-col {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--cyan-soft);
}
.footer-grid ul { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.footer-grid a {
  font-size: 0.875rem;
  color: rgba(255,255,255,0.7);
}
.footer-grid a:hover { color: #fff; }
.footer-bottom { border-top: 1px solid rgba(255,255,255,0.1); }
.footer-bottom-inner {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.25rem;
  font-size: 0.75rem;
  color: rgba(255,255,255,0.45);
}
@media (min-width: 640px) {
  .footer-bottom-inner {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }
}
@media (min-width: 1024px) {
  .footer-bottom-inner { padding-left: 2rem; padding-right: 2rem; }
}
"""


if __name__ == "__main__":
    main()
