# Sistema de Agentes de IA para Gestão e Subvenção de Editais

Protótipo acadêmico (TCC) de aplicação single-tenant baseada em agentes de IA para apoiar o ciclo de fomento público: ingestão/indexação de editais, cruzamento de elegibilidade, pontuação de aderência e geração de rascunhos de projeto.

## Stack prevista

| Camada | Tecnologia |
|--------|------------|
| API | Python 3.10+ · FastAPI |
| Banco | PostgreSQL + `pgvector` via **[Neon](https://neon.tech)** (nuvem) |
| Embeddings | `sentence-transformers` |
| Agentes | Pipeline modular (orquestrador Python; LangChain/CrewAI opcional) |
| LLM | **`none` + template** (custo zero; T-006). Ollama/API opcionais no futuro |
| Scraping (piloto/futuro) | BeautifulSoup · Playwright |

> **Sem Docker:** o ambiente padrão usa Neon. `docker-compose.yml` é opcional.

## Setup rápido (T-001 → T-003 + UI Fase A)

```powershell
# 1) Ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2) Segredos locais (Neon)
copy .env.example .env
# Edite .env e cole sua DATABASE_URL real

# 3) Validar instalação + schema Fase A
python -m scripts.check_env
python -m scripts.migrate_db

# 4) API + UI
$env:EMBEDDING_BACKEND="hashing"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- UI (landing pública): http://127.0.0.1:8000/  
- Login: http://127.0.0.1:8000/login.html  
- Criar conta: http://127.0.0.1:8000/register.html  
- Painel (área logada): http://127.0.0.1:8000/dashboard.html  
- Health: http://127.0.0.1:8000/health  
- Docs OpenAPI: http://127.0.0.1:8000/docs  
- Telas / produto: [`docs/product_ui.md`](docs/product_ui.md) · [`docs/frontend.md`](docs/frontend.md)  
- Setup detalhado: [`docs/dev_setup.md`](docs/dev_setup.md)  
- Banco Neon: [`docs/database.md`](docs/database.md)  
- Landing (Next.js): [`landing/README.md`](landing/README.md)  
- TCC — erros, testes e soluções: [`docs/TCC/diario_erros_testes_solucoes.md`](docs/TCC/diario_erros_testes_solucoes.md)  
- TCC — comparação com outras IAs (SEMENTE VIVA × Copilot): [`docs/TCC/comparacao_ias_semente_viva.md`](docs/TCC/comparacao_ias_semente_viva.md)

### Documentação do grupo (TC1 / nivelamento)

| Documento | Uso |
|-----------|-----|
| [`docs/MANUAL_COMPLETO_SADS.md`](docs/MANUAL_COMPLETO_SADS.md) | Manual técnico-funcional completo |
| [`docs/RESUMO_GRUPO_SADS.md`](docs/RESUMO_GRUPO_SADS.md) | Leitura rápida antes da banca |
| [`docs/ROTEIRO_APRESENTACAO_TC1.md`](docs/ROTEIRO_APRESENTACAO_TC1.md) | Slides, tempos e falas |
| [`docs/PERGUNTAS_E_RESPOSTAS_TC1.md`](docs/PERGUNTAS_E_RESPOSTAS_TC1.md) | Q&A com o professor |
| [`docs/ARQUITETURA_SADS.md`](docs/ARQUITETURA_SADS.md) | Arquitetura e diagramas |
| [`docs/STATUS_IMPLEMENTACAO.md`](docs/STATUS_IMPLEMENTACAO.md) | Matriz implementado × planejado |
| [`docs/GUIA_DEMONSTRACAO.md`](docs/GUIA_DEMONSTRACAO.md) | Demo ao vivo e contingência |
| [`docs/DECISOES_ARQUITETURAIS.md`](docs/DECISOES_ARQUITETURAIS.md) | ADRs |

### Autenticacao (login)

Fluxo atual:

1. Landing `/` → **Criar conta** (`/register.html`) ou **Login** (`/login.html`)
2. Register cria `company` + primeiro `employee` admin com senha
3. Login (empresa + e-mail + senha) emite token; o painel fica em `/dashboard.html`
4. Menu autenticado: Painel, Novo projeto, Materiais, Aplicacoes, Equipe — **sem** cadastrar empresa de novo

Apos puxar o codigo, rode a migration:

```powershell
python -m scripts.migrate_db
```

Variaveis em `.env`: `AUTH_SECRET`, `AUTH_TOKEN_TTL_HOURS` (ver `.env.example`).

### Landing page (opcional rebuild)

A home `/` é a landing Next.js exportada em `landing/out/`. Após editar a landing:

```powershell
cd landing
npm install
npm run build
# reinicie o uvicorn para montar /_next
```

> Python **3.10–3.12** recomendado. 3.13/3.14 podem falhar em pacotes ML em alguns ambientes.

## Árvore do repositório

```
recomendacao_fomento_agent/
├── landing/              # Landing pública (Next.js + Tailwind → export estático)
├── web/                  # UI Fase A autenticada (HTML/CSS/JS)
├── app/
│   ├── config.py
│   ├── main.py           # FastAPI + landing + static UI
│   ├── routes_fase_a.py  # APIs cadastro/projeto/dash
│   └── schemas.py
├── agents/
│   ├── scraper_agent.py  # Agente Coletor (T-005)
│   ├── retrieval_agent.py
│   ├── scoring_agent.py
│   ├── generation_agent.py
│   ├── orchestrator.py   # E2E T-042
│   └── sources/finep.py  # Fonte FINEP
├── db/
│   └── init/             # SQL de referência (ex.: CREATE EXTENSION vector)
├── scripts/
│   ├── check_env.py
│   ├── collect_editais.py
│   └── extract_pdfs.py
├── data/
│   ├── raw_pdfs/
│   ├── texts/
│   └── outputs/
├── tests/
├── docs/
├── requirements.txt
├── requirements-dev.txt
├── docker-compose.yml    # Opcional
├── .env.example
└── README.md
```

### Responsabilidade por pasta

| Pasta | Uso |
|-------|-----|
| `app/` | Gateway HTTP (`main.py`, rotas `/api/v1/...`, validação Pydantic) |
| `agents/` | `scraper`, `indexer`, `retrieval`, `scoring`, `generation`, `orchestrator` |
| `db/` | Schema SQL/Alembic, sessão PostgreSQL/`pgvector` |
| `db/init/` | SQL de referência (no Neon, rode no SQL Editor) |
| `scripts/` | Utilitários de verificação e jobs |
| `data/raw_pdfs/` | Entrada de PDFs (não versionar binários grandes) |
| `data/texts/` | Saída do extrator PDF → texto |
| `data/outputs/` | Relatórios Markdown/PDF da análise |
| `tests/` | Unitários e integração |
| `docs/` | Arquitetura, demo, privacy, resultados |

## Banco de dados (Neon + pgvector)

1. Crie um projeto no [Neon](https://console.neon.tech) (região São Paulo recomendada).
2. No **SQL Editor**, garanta a extensão:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Configure o ambiente local:

```powershell
copy .env.example .env
```

4. Cole sua `DATABASE_URL` real **somente** no `.env` (nunca no GitHub).

Guia completo: [`docs/database.md`](docs/database.md).  
Checklist: [`docs/checklist_pc_pessoal.md`](docs/checklist_pc_pessoal.md).  
**Agente Coletor / corpus (T-005):** [`docs/corpus.md`](docs/corpus.md) · manifest [`data/corpus_manifest.csv`](data/corpus_manifest.csv).  
**Migrações / seed:** [`docs/migrations.md`](docs/migrations.md).  
**LLM (T-006):** [`docs/llm.md`](docs/llm.md) — `LLM_PROVIDER=none` + fallback template.  
**Indexador (T-020):** [`docs/indexing.md`](docs/indexing.md).  
**Retrieval (T-030):** [`docs/retrieval.md`](docs/retrieval.md) — função, híbrido SQL+cosseno e como foi feito.  
**Scoring (T-040):** [`docs/scoring.md`](docs/scoring.md) — nota 0–100, breakdown e feedback.  
**Orchestrator / Generation (T-041–T-042):** [`docs/orchestrator.md`](docs/orchestrator.md).  
**Produto / 7 telas (Fase A/B):** [`docs/product_ui.md`](docs/product_ui.md) · [`docs/frontend.md`](docs/frontend.md).

### Coletar editais FINEP (automático)

```powershell
# Pipeline completo (recomendado para a UI — so FINEP fresca)
.\.venv\Scripts\python.exe -m scripts.refresh_finep_corpus --limit 20

# Ou so a coleta
.\.venv\Scripts\python.exe -m scripts.collect_editais --source finep --limit 20 --extract
```

Baixa chamadas **abertas** da FINEP (edital + anexos + metadados), extrai texto, faz seed FINEP-only e reindexa. Detalhes: [`docs/corpus.md`](docs/corpus.md).

### Banco — migrate + seed (S1)

```powershell
# 1) .env com DATABASE_URL real do Neon
copy .env.example .env

python -m scripts.index_edicts
python -m scripts.retrieve_edicts --query "startup inovacao digital" --k 5
python -m scripts.run_pipeline --query "startup inovacao digital IA" --agency FINEP
```

Detalhes: [`docs/migrations.md`](docs/migrations.md) · [`docs/retrieval.md`](docs/retrieval.md) · [`docs/orchestrator.md`](docs/orchestrator.md).

## Status do backlog

| ID | Tarefa | Status |
|----|--------|--------|
| **T-001** | Estrutura de pastas + README com árvore | **Concluída** |
| **T-002** | Banco Postgres + `pgvector` (Neon; Docker opcional) | **Concluída** |
| **T-003** | Ambiente Python + dependências | **Concluída** |
| **T-004** | Congelar escopo MVP com orientador | **Concluída** |
| **T-005** | Agente Coletor FINEP (busca automática + cache PDF) | **Concluída (piloto)** |
| **T-010–T-014** | Schema + seed corpus (edicts/companies/projects) | **Concluída** |
| **T-006** | LLM `none` + fallback template (custo zero) | **Concluída** |
| **T-020** | Indexador embeddings → `edicts.embedding` (pgvector) | **Concluída** |
| **T-030** | Retrieval Agent (busca híbrida SQL + cosseno) | **Concluída** |
| **T-040** | Scoring Agent (0–100 + forças/fraquezas) | **Concluída** |
| **T-041** | Generation Agent no pipeline (template + scoring) | **Concluída** |
| **T-042** | Orchestrator E2E + `POST /api/v1/submit-project` | **Concluída** |
| **UI-A** | Frontend 7 telas — Fase A (sem chat) | **Concluída** |
| UI-B | Chat LLM + SSO + doc formatado | Fase B (depois) |

## Escopo do MVP (lembrete)

**IN:** Neon + pgvector, **coleta automática FINEP**, embeddings, busca híbrida, scoring, geração por **template** (sem API paga), FastAPI, orquestrador, estudo de caso, **UI Fase A** (cadastros, home, upload+top3, materiais, aplicações).

**OUT / Fase B:** chat LLM, SSO, SaaS completo, scraper multi-portal em produção, billing, treino automático com feedback.

## Próximo passo

**Fase B (depois):** chat LLM, SSO, documento formatado — ver [`docs/product_ui.md`](docs/product_ui.md).
