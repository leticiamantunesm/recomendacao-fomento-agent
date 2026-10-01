# Decisões arquiteturais — SADS

Registros ADR (Architecture Decision Records) baseados no que o repositório reflete.  
Não inventar decisões sem evidência.

---

## ADR-001 — Banco Neon + pgvector (sem Docker obrigatório)

| | |
|--|--|
| **Contexto** | Precisávamos de vetores para similaridade de editais e banco gerenciado para o TCC. |
| **Alternativas** | Postgres local Docker; só arquivos; outro cloud. |
| **Decisão** | Neon + extensão `vector`; Docker opcional. |
| **Justificativa** | Setup rápido, docs em `database.md`, alinhado ao MVP. |
| **Consequências** | Dependência de rede/cloud; dados fora da máquina local. |

---

## ADR-002 — Pipeline de agentes em Python puro

| | |
|--|--|
| **Contexto** | Orquestrar coleta, índice, retrieval, score, geração. |
| **Alternativas** | LangChain/CrewAI (citados como opcionais no README). |
| **Decisão** | Módulos em `agents/` + `Orchestrator` próprio. |
| **Justificativa** | Controle de contratos, custo zero, testabilidade. |
| **Consequências** | Sem features prontas de frameworks de agentes; mais código próprio. |

---

## ADR-003 — LLM desligado por padrão (`none` + template)

| | |
|--|--|
| **Contexto** | Geração de texto de aderência sem custo e sem enviar projeto a terceiros. |
| **Alternativas** | OpenAI/Anthropic/Ollama desde o MVP. |
| **Decisão** | `LLM_PROVIDER=none`; `app/llm.py` template. |
| **Justificativa** | Custo, privacidade, previsibilidade no TC1. |
| **Consequências** | Texto menos “fluido”; chat fica Fase B com política explícita. |

---

## ADR-004 — Scoring por matriz de pesos fixos (não AHP/TOPSIS ainda)

| | |
|--|--|
| **Contexto** | Precisávamos de ranking explicável no PoC. |
| **Alternativas** | AHP, TOPSIS, só similaridade, LLM juiz. |
| **Decisão** | Matriz v2 em `SCORE_WEIGHTS` + gates. |
| **Justificativa** | Transparência imediata; implementação verificável. |
| **Consequências** | Pesos não calibrados por especialista/AHP; roadmap de multicritério formal. |

---

## ADR-005 — UI autenticada em HTML estático + landing Next

| | |
|--|--|
| **Contexto** | Entregar Fase A rápido; proposta PDF falava React/Auth.js. |
| **Alternativas** | App Next completa; SPA React. |
| **Decisão** | `web/*.html` + `app.js` para área logada; Next só na landing. |
| **Justificativa** | Velocidade de entrega do fluxo ponta a ponta. |
| **Consequências** | Divergência da proposta; possível convergência no TCC. |

---

## ADR-006 — Corpus piloto somente FINEP

| | |
|--|--|
| **Contexto** | Fonte pública com API utilizável. |
| **Alternativas** | Multi-portal desde o início. |
| **Decisão** | Coletor `sources/finep.py` + seed FINEP-only. |
| **Justificativa** | Viabilidade do piloto. |
| **Consequências** | Não generalizar resultados para “todo fomento brasileiro”. |

---

## ADR-007 — Multi-tenant por `company_id`

| | |
|--|--|
| **Contexto** | Várias organizações no mesmo banco. |
| **Alternativas** | Single-tenant (mencionado no README antigo). |
| **Decisão** | FKs `company_id` em projects/documents/applications/employees. |
| **Justificativa** | Modelo SaaS acadêmico. |
| **Consequências** | Exige authz rigorosa (ainda parcial nas rotas Fase A). |

---

## ADR-008 — Embeddings com fallback hashing

| | |
|--|--|
| **Contexto** | `sentence-transformers` pode falhar (HF/rede/Python). |
| **Alternativas** | Exigir sempre MiniLM; API de embedding paga. |
| **Decisão** | `EMBEDDING_BACKEND=auto|hashing`. |
| **Justificativa** | Demo e CI resilientes. |
| **Consequências** | Qualidade semântica menor no modo hashing. |
