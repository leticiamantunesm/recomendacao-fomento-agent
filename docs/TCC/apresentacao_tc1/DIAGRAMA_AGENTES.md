# Funcionamento da solução SADS — fluxo completo e agentes

Documento para Canva / TC1.  
Objetivo: explicar **do cadastro da empresa até o relatório**, deixando explícito o que é **ação de agente** e o que **não é**.

---

## Legenda (usar no Canva)

| Símbolo | Significado |
|---------|-------------|
| **AGENTE** | Módulo em `agents/` com responsabilidade de IA/pipeline (coletar, indexar, buscar, pontuar, gerar, orquestrar) |
| **NÃO É AGENTE** | UI, autenticação, CRUD, upload, banco, regras de produto — infraestrutura e aplicação |

---

## Duas faixas que rodam em momentos diferentes

O sistema não começa no PDF do usuário. Há **duas faixas**:

```text
FAIXA A — PREPARAÇÃO DO CORPUS (offline / operação)
  Coletor → Indexador → Banco de editais
  (roda antes ou em paralelo; não é o clique do usuário)

FAIXA B — JORNADA DO USUÁRIO (online)
  Cadastro → Login → Upload → Avaliação (agentes) → Relatório
```

Sem a Faixa A, a Faixa B não tem com o que comparar.

---

## Diagrama-mestre (Canva)

```text
═══════════════════════════════════════════════════════════════
 FAIXA A — CORPUS FINEP                    [maioria = AGENTE]
═══════════════════════════════════════════════════════════════

  API FINEP
      │
      ▼
  ┌─────────────────────┐
  │ AGENTE Coletor      │  ScraperAgent
  │ baixa chamadas/PDFs │
  └──────────┬──────────┘
             ▼
  ┌─────────────────────┐
  │ NÃO É AGENTE        │  extract / seed no Neon
  │ grava editais       │
  └──────────┬──────────┘
             ▼
  ┌─────────────────────┐
  │ AGENTE Indexador    │  IndexerAgent
  │ embeddings → pgvector│
  └──────────┬──────────┘
             ▼
        [(edicts)]  corpus público de editais


═══════════════════════════════════════════════════════════════
 FAIXA B — USUÁRIO ATÉ O RELATÓRIO
═══════════════════════════════════════════════════════════════

  1. Cadastro empresa + admin     ── NÃO É AGENTE (auth / CRUD)
  2. Login                        ── NÃO É AGENTE (sessão)
  3. Upload PDF do projeto        ── NÃO É AGENTE (API + disco)
  4. Extração de texto do PDF     ── NÃO É AGENTE (utilitário)
  5. Formulário / perfil          ── NÃO É AGENTE (UI + PATCH)
             │
             ▼  (usuário clica Avaliar / evaluate)
  ┌─────────────────────────────────────────────┐
  │         ZONA AGENTICA (núcleo do TCC)       │
  │                                             │
  │   AGENTE Retrieval  →  candidatos FINEP     │
  │           ↓                                 │
  │   AGENTE Scoring    →  ranking + lacunas    │
  │           ↓                                 │
  │   AGENTE Generation →  rascunho (opcional / │
  │                        pipeline CLI)        │
  │           ↓                                 │
  │   AGENTE Orquestrador (CLI/API E2E)         │
  │   na UI: retrieve+score encadeados na rota  │
  └──────────────────────┬──────────────────────┘
                         ▼
  6. Persistir applications       ── NÃO É AGENTE (banco)
  7. Relatório na UI              ── NÃO É AGENTE (front)
  8. Link para página FINEP       ── NÃO É AGENTE (URL do edital)
```

---

## Passo a passo da Faixa B (o que o usuário vê)

### Passo 1 — Cadastro da organização
| | |
|--|--|
| **O que acontece** | Razão social, CNPJ (consulta opcional), admin, senha → cria `companies` + `employees` |
| **Quem faz** | **NÃO É AGENTE** — `routes_auth` / formulário `register.html` |
| **Por quê não é agente** | Cadastro e autenticação; sem decisão sobre editais |

### Passo 2 — Login
| | |
|--|--|
| **O que acontece** | Empresa + e-mail + senha → token de sessão |
| **Quem faz** | **NÃO É AGENTE** — auth |
| **Por quê** | Controle de acesso multi-tenant |

### Passo 3 — Envio do PDF do projeto
| | |
|--|--|
| **O que acontece** | Upload → arquivo em `data/uploads/<company_id>/` → registro em `projects` (+ documento) |
| **Quem faz** | **NÃO É AGENTE** — API `POST /projects` + UI |
| **Por quê** | Persistência de arquivo; ainda não há ranking |

### Passo 4 — Extração de texto e formulário
| | |
|--|--|
| **O que acontece** | Lê o PDF, preenche campos (título, resumo, orçamento…); usuário revisa |
| **Quem faz** | **NÃO É AGENTE** — utilitário de extração + UI de edição |
| **Obs.** | É pré-processamento. **Não** é Retrieval nem Scoring |

### Passo 5 — Avaliação (entra a zona agentica)
| | |
|--|--|
| **O que acontece** | Perfil da empresa + texto do projeto são enviados ao motor |
| **Disparo** | **NÃO É AGENTE** — botão / `POST .../evaluate` (só dispara) |
| **Dentro do motor** | ver seção seguinte (**AGENTes**) |

### Passo 6 — Relatório e recomendações
| | |
|--|--|
| **O que acontece** | Ranking, score, breakdown, lacunas, plano, link FINEP |
| **Quem gera os números** | **AGENTE Scoring** (e candidatos do **Retrieval**) |
| **Quem desenha a tela** | **NÃO É AGENTE** — `project-evaluate.html` |
| **Quem grava no banco** | **NÃO É AGENTE** — tabela `applications` |

---

## Zona agentica — o que cada agente faz (foco do TCC)

### AGENTE 1 — Coletor (`ScraperAgent`) · Faixa A

```text
Entrada:  pedido de coleta (ex.: chamadas abertas FINEP)
Processo: consulta API FINEP, baixa PDFs/anexos, monta metadados
Saída:    arquivos + manifest / metadados para seed
```

- **É agente:** sim — coleta autônoma de fontes externas.  
- **Não faz:** login de usuário, upload de projeto, score final.

---

### AGENTE 2 — Indexador (`IndexerAgent`) · Faixa A

```text
Entrada:  texto dos editais no banco
Processo: gera embedding (vetor)
Saída:    edicts.embedding no Neon/pgvector
```

- **É agente:** sim — prepara representação semântica do corpus.  
- **Não faz:** comparar com o projeto do usuário (isso é Retrieval).

---

### AGENTE 3 — Retrieval (`RetrievalAgent`) · Faixa B (avaliação)

```text
Entrada:  ProjectQuery (texto do projeto) + CompanyProfile (porte, TRL, áreas, UF)
Processo: 1) filtros SQL (órgão, elegibilidade estrutural)
          2) embedding da query do projeto
          3) ordenação por similaridade de cosseno vs editais
Saída:    Top-k EdictMatch (candidatos + reasons)
```

- **É agente:** sim — **busca híbrida** (estrutura + semântica).  
- **Não faz:** nota final 0–100 completa (isso é Scoring); não baixa FINEP de novo.

---

### AGENTE 4 — Scoring (`ScoringAgent`) · Faixa B (avaliação)

```text
Entrada:  lista de EdictMatch + perfil/projeto
Processo: matriz v2 de pesos + gates (prazo, porte, TRL, região…)
Saída:    ScoreReport[] ordenados
          score, breakdown, strengths, weaknesses, eligible, summary
```

Pesos (PoC):

```text
0,30 similaridade · 0,25 tema · 0,15 TRL · 0,15 porte · 0,10 região · 0,05 orçamento
```

- **É agente:** sim — **decisão multicritério explicável**.  
- **Não faz:** layout do relatório HTML; não autentica usuário.

---

### AGENTE 5 — Generation (`GenerationAgent`) · pipeline E2E / CLI

```text
Entrada:  projeto + edital + resultado do scoring
Processo: monta rascunho estruturado
Saída:    Markdown (relatório textual)
PoC:      LLM_PROVIDER=none → template local (SEM LLM externo)
```

- **É agente:** sim — camada de geração de texto de apoio.  
- **Na UI atual do evaluate:** o “relatório visual” é montado no front com os dados do Scoring; o Generation entra de forma completa no **Orquestrador / CLI**.  
- **Não faz:** escolher o ranking (já veio do Scoring).

---

### AGENTE 6 — Orquestrador (`Orchestrator`)

```text
Entrada:  PipelineRequest (título, texto, perfil empresa, k…)
Processo: Retrieval → Scoring → Generation → exporta MD/JSON
Saída:    pipeline_report_*.md + pipeline_last.json
```

- **É agente:** sim — **coordena** os outros agentes (não substitui o trabalho deles).  
- **Na UI `evaluate`:** a rota FastAPI encadeia Retrieval + Scoring (orquestração “embutida” na API).  
- **Não é agente:** a própria rota HTTP, o HTML, o login.

---

## Tabela rápida: agente × não agente

| Etapa | Componente | Agente? |
|-------|------------|---------|
| Cadastro / login | Auth + UI | **Não** |
| Consulta CNPJ | API externa utilitária | **Não** |
| Upload PDF | API + storage | **Não** |
| Extração texto PDF | Script/utilitário | **Não** |
| Edição do formulário | UI | **Não** |
| Coleta FINEP | `ScraperAgent` | **Sim** |
| Indexar editais | `IndexerAgent` | **Sim** |
| Buscar candidatos | `RetrievalAgent` | **Sim** |
| Pontuar / rankear | `ScoringAgent` | **Sim** |
| Rascunho MD (pipeline) | `GenerationAgent` | **Sim** |
| Encadear E2E | `Orchestrator` | **Sim** |
| Salvar `applications` | Banco / API | **Não** |
| Tela do relatório | Front | **Não** |
| Link “Abrir FINEP” | URL já no edital | **Não** |
| Tema claro/escuro, menu | Front | **Não** |

---

## Frase para a banca (30 s)

> “Do cadastro ao upload, o sistema é aplicação web clássica — multi-tenant e autenticação.  
> A parte agentica começa quando o corpus FINEP é coletado e indexado, e se manifesta para o usuário no **evaluate**: o **Retrieval** encontra candidatos, o **Scoring** gera ranking explicável, e o **Orquestrador** (ou a rota que o encadeia) entrega o resultado.  
> A interface só **apresenta** o que os agentes decidiram — não é ela que calcula a aderência.”

---

## Dados: o que os agentes tocam

| Dado | Agente que usa | Privado? |
|------|----------------|----------|
| Editais FINEP + embeddings | Coletor, Indexador, Retrieval | Fonte pública |
| Texto do projeto | Retrieval, Scoring (, Generation) | **Privado da empresa** |
| Perfil (porte, TRL, UF) | Retrieval, Scoring | **Privado** |
| Recomendações gravadas | Persistência pós-Scoring | **Privado** |

- Projeto **não** treina modelo.  
- PoC: **sem LLM externo**; Generation em template local.  
- Chat com LLM = **próximo passo** (opt-in; preferir local / retenção zero).

---

## Como desenhar no Canva (sugestão)

1. **Slide A:** Faixa A (3 caixas agenticas + banco) — “antes do usuário”.  
2. **Slide B:** Timeline horizontal Passos 1→8 com etiquetas verde=agente / cinza=não agente.  
3. **Slide C:** Zoom na zona agentica Retrieval → Scoring → (Generation) → Orquestrador.  
4. **Slide D:** Tabela “agente × não agente” (resumo).

Cor sugerida: ciano = **AGENTE** · cinza = **NÃO É AGENTE**.
