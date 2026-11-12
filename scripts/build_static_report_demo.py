"""Gera HTML estático autocontido do relatório (guardrail) para GitHub Pages / abrir offline."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "web" / "report.css").read_text(encoding="utf-8")
OUT = ROOT / "docs" / "demo" / "sads-relatorio-guardrail.html"
INDEX = ROOT / "docs" / "demo" / "index.html"
README = ROOT / "docs" / "demo" / "README.md"

HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SADS — Demo relatório (guardrail) · Solar Bairro</title>
  <meta name="description" content="Demonstração estática do relatório SADS com guardrail: sem % em orientação BNDES fora da base indexada." />
  <style>
__CSS__
  .demo-banner {
    margin: 12px 28px 0;
    padding: 12px 14px;
    border-radius: 12px;
    border: 1px solid rgba(46,199,255,.35);
    background: rgba(46,199,255,.12);
    color: #cfefff;
    font-size: 13px;
  }
  .demo-banner strong { color: #fff; }
  .brand-text { font-family: var(--font-display); font-weight: 800; letter-spacing: .04em; color: #fff; }
  </style>
</head>
<body class="report-body">
  <div class="brand-ribbon" aria-hidden="true"></div>
  <div class="demo-banner">
    <strong>Demo estática (sem API).</strong>
    Caso ilustrativo: modernização solar sem P&D — o SADS <em>não</em> mostra % de “aprovação BNDES”;
    mostra orientação fora da base indexada (piloto FINEP/FAPESP). Abra este arquivo localmente ou via GitHub Pages.
  </div>
  <div class="report-app">
    <header class="report-topbar">
      <div class="brand" aria-label="SADS">
        <span class="brand-text">SADS</span>
      </div>
      <div class="top-actions">
        <button class="ghost" type="button" onclick="window.print()">Imprimir / PDF</button>
        <a class="primary" href="#ranking">Ver ranking</a>
      </div>
    </header>

    <div class="layout">
      <aside class="sidebar">
        <div class="project-switcher">
          <div class="eyebrow">Projeto analisado</div>
          <strong id="side-title">Solar Bairro</strong>
          <small class="muted" id="side-meta">Modernização / Crédito · demo guardrail</small>
        </div>
        <nav class="side-nav">
          <a href="#resumo" class="active">Resumo <span>01</span></a>
          <a href="#alertas">Alertas <span>02</span></a>
          <a href="#ranking">Ranking <span>03</span></a>
          <a href="#porque">Por que #1 <span>04</span></a>
          <a href="#proximos">Próximos passos <span>05</span></a>
        </nav>
      </aside>

      <main class="report-main">
        <div class="page-head">
          <div>
            <div class="eyebrow">Relatório de recomendação de fomento</div>
            <h1 id="page-title">BAD_02 — Solar Bairro (instalação fotovoltaica)</h1>
            <div class="muted" id="page-subtitle">Aquisição e instalação de placas solares prontas — sem adicionalidade de P&amp;D evidenciada.</div>
            <div id="track-badge" class="track-badge modernization_credit">Modernização / Crédito</div>
            <p id="track-hint" class="track-hint">Sem match típico de subvenção P&amp;D na base: o caminho tende a crédito/consultoria (orientação — não é aprovação BNDES).</p>
          </div>
          <div class="status warn" id="page-status">Trilha crédito · orientação</div>
        </div>

        <section id="resumo" class="hero">
          <article class="card recommendation" id="hero-rec"></article>
          <article class="card score-card" id="hero-score"></article>
        </section>

        <section class="section kpis" id="kpi-row"></section>

        <section id="alertas" class="section">
          <div class="section-head">
            <h2>Alertas e avisos</h2>
            <span class="section-note">Leia antes de qualquer encaminhamento</span>
          </div>
          <div id="alert-banner" class="alert-banner warn"></div>
          <article class="card alert-panel">
            <div class="alert-list" id="alertas-body"></div>
            <div class="suggest-row" id="sugestoes-body"></div>
            <div class="blocked-mini" id="bloqueados-body"></div>
          </article>
        </section>

        <section id="ranking" class="section">
          <div class="section-head">
            <h2>Ranking de programas</h2>
            <span class="section-note">Redirects = orientação fora da base (sem %)</span>
          </div>
          <article class="card ranking" id="ranking-body"></article>
          <div class="card detail-panel open" id="rank-detail"></div>
        </section>

        <section id="porque" class="section">
          <div class="section-head">
            <h2>Por que esta orientação (fora da base)?</h2>
            <span class="section-note">Orientação fora da base — sem % de aderência (não é linha BNDES aprovada)</span>
          </div>
          <div id="porque-body" class="two-col"></div>
        </section>

        <section id="proximos" class="section">
          <div class="section-head">
            <h2>Próximos passos</h2>
            <span class="section-note">Checklist sugerido</span>
          </div>
          <article class="card">
            <div class="action-list">
              <div class="action"><span class="check">1</span><div><strong>Não tratar como aprovação BNDES</strong><div class="muted">O anel “—” indica ausência de match indexado.</div></div><span class="deadline">Imediato</span></div>
              <div class="action"><span class="check">2</span><div><strong>Consultar agente financeiro / portal BNDES</strong><div class="muted">Crédito Capex (ex.: energia) via repassador — fora do SADS.</div></div><span class="deadline">0–7 dias</span></div>
              <div class="action"><span class="check">3</span><div><strong>Avaliar Sebraetec / fomento estadual</strong><div class="muted">Consultoria e linhas regionais conforme UF.</div></div><span class="deadline">0–14 dias</span></div>
            </div>
          </article>
        </section>

        <p class="footer-note">SADS · demo estática guardrail · score ≠ aprovação · corpus piloto FINEP/FAPESP · BNDES só orientação ampla (ADR-009/010)</p>
      </main>
    </div>
  </div>

  <script>
(function () {
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));

  const DEMO = {
    diagnosis: {
      has_technological_risk: false,
      report_track: "modernization_credit",
      report_track_label: "Modernização / Crédito",
      report_track_hint:
        "Sem match típico de subvenção P&D na base: o caminho tende a crédito/consultoria (orientação — não é aprovação BNDES).",
      primary_path: "credito",
      budget_math_inconsistency: false,
      ineligible_budget_items: [],
      alerts: [
        "Perfil de modernização/aquisição (sem P&D evidenciado): subvenção econômica não é o caminho. Não encaminhar como subvenção P&D: avalie crédito/consultoria/incentivo (orientação fora dos programas indexados do SADS)."
      ]
    },
    redirect_suggestions: [
      {
        name: "Sebraetec",
        kind: "consultoria",
        reason: "Consultoria e implantação tecnológica sem exigir P&D."
      },
      {
        name: "BNDES — crédito e financiamento",
        kind: "credito",
        reason:
          "Orientação fora da base indexada do SADS: caminho típico é crédito (consultar portal BNDES / agente financeiro). Não é match de linha específica nem aprovação de financiamento."
      },
      {
        name: "Desenvolve SP (exemplo estadual)",
        kind: "credito_estadual",
        reason: "Crédito/fomento estadual — verificar elegibilidade no agente local."
      }
    ],
    applications: [
      {
        id: "1",
        rank_position: 1,
        edict_external_id: "redirect-bndes-credito-e-financiamento",
        edict_title: "BNDES — crédito e financiamento",
        agency: "BNDES",
        score: 74,
        status: "recommended",
        strengths: [
          "Perfil Capex/modernização (placas prontas)",
          "Consultar agente financeiro / portal oficial — o SADS não lista linha específica",
          "Separar orientação de match indexado (FINEP/FAPESP)"
        ],
        weaknesses: ["Sem linha específica na base do SADS", "Não usar % interno como aprovação"],
        summary:
          "Orientação fora da base indexada do SADS: caminho típico é crédito (consultar portal BNDES / agente financeiro). Não é match de linha específica nem aprovação de financiamento.",
        breakdown: { instrument: "credito", instrument_label: "crédito", why_this: "Orientação fora da base — modernização sem P&D." }
      },
      {
        id: "2",
        rank_position: 2,
        edict_external_id: "redirect-sebraetec",
        edict_title: "Sebraetec",
        agency: "Sebrae",
        score: 71,
        status: "recommended",
        strengths: ["Consultoria sem exigir P&D", "Apoio à implantação"],
        weaknesses: ["Não é edital FINEP indexado"],
        summary: "Orientação de consultoria (fora da base de editais do SADS).",
        breakdown: { instrument: "parceria", instrument_label: "parceria / consultoria" }
      }
    ],
    blocked_applications: [
      {
        edict_title: "FINEP — chamada ilustrativa de subvenção P&D",
        edict_external_id: "finep-demo-blocked",
        weaknesses: ["Bloqueado: Fit de instrumento 0% — projeto sem risco tecnológico / P&D"],
        breakdown: { instrument: "subvencao", block_reasons: ["Fora da trilha de crédito — exige P&D"] }
      }
    ]
  };

  function isRedirect(app) {
    return String(app?.edict_external_id || "").startsWith("redirect-");
  }

  const top = DEMO.applications[0];

  document.getElementById("hero-rec").innerHTML = `
    <div class="rank">ORIENTAÇÃO (FORA DA BASE INDEXADA)</div>
    <h2 class="program-title">${esc(top.edict_title)}</h2>
    <p class="muted">${esc(top.summary)}</p>
    <div class="program-meta">
      <span class="chip">Modernização / Crédito</span>
      <span class="chip">sem % de aderência</span>
      <span class="chip">Orientação (fora da base)</span>
    </div>
    <div class="reasons">
      ${top.strengths.slice(0, 3).map((r) => `<div class="reason">${esc(r)}</div>`).join("")}
    </div>`;

  document.getElementById("hero-score").innerHTML = `
    <div class="eyebrow">Match na base</div>
    <div class="score-ring" style="background: conic-gradient(var(--primary) 0 0%, rgba(255,255,255,0.08) 0% 100%)">
      <div class="score-number">—</div>
    </div>
    <div class="range mid">Sem programa indexado</div>
    <small class="muted">Orientação de caminho — não use % como aprovação</small>`;

  document.getElementById("kpi-row").innerHTML = `
    <article class="card kpi"><div class="label">Trilha</div><div class="value" style="font-size:1rem">Modernização / Crédito</div><div class="sub">credito</div></article>
    <article class="card kpi"><div class="label">No ranking</div><div class="value">2</div><div class="sub">1 fora da trilha / bloqueado(s)</div></article>
    <article class="card kpi"><div class="label">Orçamento</div><div class="value" style="font-size:1rem">Capex solar</div><div class="sub">demo</div></article>
    <article class="card kpi"><div class="label">Tipo (#1)</div><div class="value" style="font-size:1rem">Orientação</div><div class="sub">sem %</div></article>`;

  document.getElementById("alert-banner").innerHTML = `
    <div class="alert-banner-kicker">↗ Trilha: Modernização / Crédito</div>
    <strong>Sem match de programa na base indexada do SADS</strong>
    <p>Orientação: crédito, consultoria ou incentivo fiscal. BNDES aparece só como instituição ampla — não como linha/aprovação.</p>`;

  document.getElementById("alertas-body").innerHTML = `
    <div class="alert-item warn">
      <div class="dot"></div>
      <div><strong>Caminho: crédito / modernização (orientação)</strong>
      <p>Não há enquadramento típico de subvenção P&amp;D nos programas indexados (FINEP/FAPESP…). O ranking pode sugerir crédito/consultoria como orientação — isso não é match de linha BNDES nem aprovação.</p></div>
      <span class="tag">Encaminhamento</span>
    </div>`;

  document.getElementById("sugestoes-body").innerHTML =
    `<div class="eyebrow" style="margin-bottom:6px">Orientações fora da base (sem % / sem aprovação)</div>` +
    DEMO.redirect_suggestions
      .map((r) => `<div class="suggest-chip"><strong>${esc(r.name)}</strong><span>${esc(r.reason)}</span></div>`)
      .join("");

  document.getElementById("bloqueados-body").innerHTML =
    `<div class="eyebrow" style="margin-bottom:6px">Fora da trilha (exigem P&amp;D / subvenção)</div>` +
    DEMO.blocked_applications
      .map((b) => `<div class="row"><strong>${esc(b.edict_title)}</strong><span>Fora da trilha — exige P&amp;D</span></div>`)
      .join("");

  document.getElementById("ranking-body").innerHTML = DEMO.applications
    .map((a) => {
      const orient = isRedirect(a);
      return `<div class="program-row">
        <div class="medal">${esc(a.rank_position)}</div>
        <div><strong>${esc(a.edict_title)}</strong>
          <div class="muted">${orient ? "orientação (fora da base)" : esc(a.breakdown.instrument_label)}</div></div>
        <div class="hide-tablet"><strong>—</strong><div class="muted">orçamento projeto</div></div>
        <div class="hide-tablet"><span class="chance medium">${orient ? "Orientação (fora da base)" : "—"}</span></div>
        <div class="fit">${orient ? "—" : Math.round(a.score) + "%"}</div>
        <div class="arrow">›</div>
      </div>`;
    })
    .join("");

  document.getElementById("rank-detail").innerHTML = `
    <div class="eyebrow">Orientação (fora da base)</div>
    <h3 style="margin-top:6px">${esc(top.edict_title)}</h3>
    <p class="muted">Orientação (fora da base) · sem % de aderência (não é edital indexado)</p>
    <p>${esc(top.summary)}</p>
    <p><strong>Pontos a favor:</strong> ${top.strengths.map(esc).join(" · ")}</p>
    <p><strong>Atenções:</strong> ${top.weaknesses.map(esc).join(" · ")}</p>`;

  document.getElementById("porque-body").innerHTML = `
    <article class="card">
      <p class="muted">Sem gráfico de aderência: isto é orientação fora dos programas indexados (não use % como aprovação BNDES/FINEP).</p>
    </article>
    <article class="card">
      <h3>Por que esta orientação?</h3>
      <p>Não há match com programa na base do SADS; o caminho tende a crédito/consultoria/incentivo fiscal.</p>
      <p class="muted" style="margin-top:12px">${esc(DEMO.diagnosis.report_track_hint)}</p>
      <h3 style="margin-top:20px">Alternativa na mesma trilha</h3>
      <p class="muted">Também há orientação: Sebraetec (fora da base — sem %).</p>
    </article>`;
})();
  </script>
</body>
</html>
'''

def main() -> None:
    html = HTML.replace("__CSS__", CSS)
    OUT.write_text(html, encoding="utf-8")
    INDEX.write_text(
        """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0; url=sads-relatorio-guardrail.html" />
  <title>SADS demo</title>
  <link rel="canonical" href="sads-relatorio-guardrail.html" />
</head>
<body>
  <p><a href="sads-relatorio-guardrail.html">Abrir demo do relatório SADS (guardrail)</a></p>
</body>
</html>
""",
        encoding="utf-8",
    )
    README.write_text(
        """# Demo estática — relatório SADS (guardrail)

Arquivo autocontido (CSS + HTML + JS), **sem API**.

## Abrir localmente

Abra no navegador:

`docs/demo/sads-relatorio-guardrail.html`

(duplo clique ou arrastar para o Chrome/Edge/Firefox)

## GitHub Pages

1. Settings do repositório → **Pages**
2. Source: Deploy from branch → pasta `/docs`
3. URL típica:

`https://<usuario>.github.io/<repositorio>/demo/`

ou

`https://<usuario>.github.io/<repositorio>/demo/sads-relatorio-guardrail.html`

## O que a demo mostra

Caso **Solar Bairro** (modernização sem P&D):

- anel de score **—** (não 74%)
- BNDES como **orientação fora da base**
- subvenção FINEP ilustrativa **bloqueada**
- textos: match ≠ aprovação

As mudanças do guardrail também estão no app vivo: `web/project-evaluate.html`.
""",
        encoding="utf-8",
    )
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(f"Wrote {INDEX}")
    print(f"Wrote {README}")


if __name__ == "__main__":
    main()
