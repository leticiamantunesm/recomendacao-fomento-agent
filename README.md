# Sistema de Agentes de IA para Gestão e Subvenção de Editais

Protótipo acadêmico (TCC) de aplicação single-tenant baseada em agentes de IA para apoiar o ciclo de fomento público: ingestão/indexação de editais, cruzamento de elegibilidade, pontuação de aderência e geração de rascunhos de projeto.

## Stack prevista

| Camada | Tecnologia |
|--------|------------|
| API | Python 3.10+ · FastAPI |
| Banco | PostgreSQL + `pgvector` |
| Embeddings | `sentence-transformers` |
| Agentes | Pipeline modular (orquestrador Python; LangChain/CrewAI opcional) |
| LLM | Ollama e/ou API externa (com fallback) |
| Scraping (piloto/futuro) | BeautifulSoup · Playwright |

## Árvore do repositório (T-001)

```
recomendacao_fomento_agent/
├── app/                  # API FastAPI (rotas, schemas, serviços)
├── agents/               # Agentes especializados + orquestrador
├── db/                   # Conexão, modelos e migrações
├── data/
│   ├── raw_pdfs/         # PDFs brutos de editais/projetos
│   ├── texts/            # Textos extraídos dos PDFs
│   └── outputs/          # Relatórios e rascunhos gerados
├── tests/                # Testes automatizados
├── docs/                 # Documentação técnica e material do TCC
├── Plano_Sprints_TCC_Agentes_Editais_Set_Nov_2026.xlsx
└── README.md
```

### Responsabilidade por pasta

| Pasta | Uso |
|-------|-----|
| `app/` | Gateway HTTP (`main.py`, rotas `/api/v1/...`, validação Pydantic) |
| `agents/` | `scraper`, `indexer`, `retrieval`, `scoring`, `generation`, `orchestrator` |
| `db/` | Schema SQL/Alembic, sessão PostgreSQL/`pgvector` |
| `data/raw_pdfs/` | Entrada de PDFs (não versionar binários grandes) |
| `data/texts/` | Saída do extrator PDF → texto |
| `data/outputs/` | Relatórios Markdown/PDF da análise |
| `tests/` | Unitários e integração |
| `docs/` | Arquitetura, demo, privacy, resultados |

## Status do backlog

| ID | Tarefa | Status |
|----|--------|--------|
| **T-001** | Estrutura de pastas + README com árvore | **Concluída** |
| T-002 | `docker-compose.yml` com pgvector | Pendente |
| T-003 | Ambiente Python + dependências | Pendente |

## Escopo do MVP (lembrete)

**IN:** Docker + pgvector, ingestão offline de editais, embeddings, busca híbrida, scoring, geração RAG, FastAPI, orquestrador, estudo de caso.

**OUT (trabalho futuro):** SaaS completo, scraper multi-portal em produção, auth enterprise, billing.

## Próximo passo

Implementar **T-002**: `docker-compose.yml` com PostgreSQL e extensão `pgvector`.
