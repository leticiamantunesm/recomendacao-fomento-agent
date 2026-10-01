# Produto — telas da plataforma (TCC)

Documento de produto alinhado ao escopo congelado com o orientador (T-004) e ao plano de frontend.

**Stack UI:** páginas estáticas em `web/`, servidas pelo FastAPI (mesmo origin). Sem React/Node na Fase A.  
**Chat:** Fase B (fora desta entrega).  
**SSO:** Fase B; na Fase A o funcionário se cadastra manualmente vinculado à empresa.

---

## Visão das 7 telas

| # | Tela | Fase | Objetivo |
|---|------|------|----------|
| 1 | Cadastro da empresa | A | Uma empresa por “conta” na plataforma; dados usados no cruzamento de elegibilidade |
| 2 | Cadastro do funcionário | A | Vários funcionários por empresa; contexto de área/papel para projetos e fomento |
| 3 | Página inicial + dashboard | A | Identidade (usuário + empresa), atalhos e métricas de uso/resultado |
| 4 | Novos projetos + relatório | A | PDF + formulário → agentes → relatório (wireframe) com top 5, diagnóstico, lacunas e plano |
| 5 | Chat | **B** | Perguntas sobre projeto/editais e geração de documento formatado (LLM) |
| 6 | Materiais subidos | A | Repositório de documentos |
| 7 | Projetos aplicados | A | Registrar aceite/recusa no fomento; base para acurácia e melhoria futura |

```text
Empresa ──< Funcionários
   │
   ├── Projetos ──< Documentos
   │       │
   │       └── Aplicações (project × edital × status/outcome)
   │
   └── Documentos (nível empresa)
```

---

## Tela 1 — Cadastro da empresa

**Entrada (campos-alvo Fase A):**

- Razão social / nome fantasia  
- CNPJ  
- Porte (**automatico via consulta publica do CNPJ**; editavel)  
- Número de funcionários  
- Faturamento anual aproximado (R$)  
- UF / município  
- CNAE (texto ou código)  
- Áreas de atuação (lista)  
- Contato institucional (e-mail / telefone)

> TRL institucional **nao** e pedido no cadastro (empresas em geral nao sabem informar).

**Persistência:** tabela `companies` (já existe parcialmente: `name`, `size`, `trl`, `areas`, `cnpj`) — enriquecer na migração Fase A.

**Uso futuro:** filtros e scoring de elegibilidade (porte, TRL, área, etc.).

---

## Tela 2 — Cadastro do funcionário

**Regra:** 1 empresa na plataforma; N funcionários ligados a ela.

**Campos-alvo Fase A:**

- Nome  
- E-mail (identificador de login demo)  
- Área / departamento  
- Cargo / papel (ex.: P&D, financeiro, direção)  
- Telefone (opcional)  
- Notas relevantes a fomento (texto livre curto)

**SSO:** desejável, mas **Fase B**. Fase A = formulário local + sessão leve (`localStorage` / cookie com `employee_id`).

**Persistência:** nova tabela `employees`.

---

## Tela 3 — Página inicial

**Cabeçalho:** nome do usuário logado + nome da empresa.

**Botões / atalhos:**

1. Subir novos projetos (→ tela 4)  
2. Chat (→ **desabilitado / “em breve”** na Fase A; ativo na B)  
3. Materiais subidos (→ tela 6)  
4. Projetos aplicados (→ tela 7)

**Dashboard (métricas Fase A):**

| Métrica | Fonte |
|---------|--------|
| Projetos enviados / avaliados | `projects` |
| Aplicações por status | `applications.status` |
| Aprovados / rejeitados | outcomes informados pelo usuário |
| Taxa de acerto do top 3 | quando `approved`, edital estava no top 3 sugerido? |
| Economia estimada (R$) | soma de valores informados em aplicações **aprovadas** (campo manual; não inventar) |

---

## Tela 4 — Subir projetos e avaliar

**Fluxo:**

1. Upload de PDF do projeto/proposta  
2. Extração de texto + preenchimento automático de formulário (heurístico na Fase A)  
3. Usuário **edita** qualquer campo  
4. Continuar → agentes (Retrieval → Scoring)  
5. Abrir **relatório de recomendação** (`project-evaluate.html`, baseado em `docs/TCC/wireframe_relatorio_fomento.html`): resumo #1, score, KPIs, diagnóstico, ranking top 5, critérios da matriz v2, lacunas e plano de ação  
6. Usuário pode “aplicar / marcar como submetido” a um dos três → cria/atualiza `applications`

**Backend reaproveitado:** lógica de [`agents/orchestrator.py`](../agents/orchestrator.py) / scoring existente; API dedicada por `project_id`.

**Geração longa de documento formatado para órgão:** Fase B (chat / generation rica).

---

## Tela 5 — Chat (somente Fase B)

Escopo fechado (quando existir):

- Perguntas sobre um projeto já enviado  
- Perguntas gerais sobre fomentos/editais indexados  
- Pedir geração de documento com formatação adequada após checar requisitos do edital escolhido  

**Fora do escopo do chat:** qualquer outra função da plataforma.

**Provedor preferencial na B:** Ollama local (dados não saem da máquina) ou API paga documentada. Hoje o MVP usa `LLM_PROVIDER=none` + template.

---

## Tela 6 — Materiais subidos

Repositório simples:

- Lista de arquivos (nome, tipo, data, projeto vinculado se houver)  
- Upload adicional  
- Download / abertura  

Sem editor colaborativo na Fase A.

---

## Tela 7 — Acompanhamento dos projetos aplicados

Após sugerir/submeter a um edital, o usuário atualiza:

- Status: em análise / aprovado / rejeitado / cancelado  
- Valor aprovado (opcional)  
- Notas / motivo  

**Valor para o TCC:**

- Medir acurácia das recomendações  
- Acumular feedback para melhorar scoring na Fase B+

---

## Fase A vs Fase B (checklist)

### Fase A (implementar)

- [x] Schema enriquecido + `employees`, `documents`, `applications`  
- [x] Telas 1, 2, 3, 4, 6, 7  
- [x] APIs REST correspondentes + upload PDF  
- [x] Dashboard com métricas reais a partir do Neon  
- [x] Nav com Chat marcado “Fase B”  
- [x] Docs + smoke E2E  

### Fase B (depois)

- [ ] Chat (tela 5) + geração de documento formatado  
- [ ] SSO  
- [ ] Uso de outcomes para retreino / ajuste de pesos  
- [ ] (Opcional) disparar coleta FINEP pela UI com autenticação  

---

## Segurança e dados

- Segredos só no servidor (`.env`).  
- PDFs e textos em disco local (`data/`) + metadados no Neon.  
- Sem expor coleta aberta na web na Fase A.  
- CNPJ e dados cadastrais tratados como sensíveis: só via API autenticada (sessão demo na A).  

---

## Histórico de decisões

| Data | Decisão |
|------|---------|
| 2026-09 | Escopo congelado com orientador (T-004) |
| 2026-09 | Stack UI = estático + FastAPI (sem Node) |
| 2026-09 | Chat = Fase B; SSO = Fase B |
| 2026-09 | 7 telas documentadas; Fase A = telas 1–4, 6–7 |
