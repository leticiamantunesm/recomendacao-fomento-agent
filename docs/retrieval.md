# Retrieval Agent (T-030) — função e desenvolvimento

## 1. Função do agente (o que ele faz)

O **Retrieval Agent** (Agente de Adequação e Busca) é responsável por **cruzar o perfil da empresa + texto do projeto com os editais já indexados no Neon** e devolver uma lista ranqueada dos mais aderentes.

Em uma frase:

> Dado um projeto e uma empresa, encontrar os *k* editais mais compatíveis, combinando **filtros estruturados (SQL)** com **similaridade semântica (pgvector / cosseno)**, e explicar **por que** cada edital entrou no ranking.

### Entradas

| Entrada | Conteúdo |
|---------|----------|
| `ProjectQuery` | `title` + `text` do projeto (ou consulta avulsa) |
| `CompanyProfile` | `name`, `size` (porte), `trl`, `areas[]` |
| Parâmetros | `k`, `agency`, `year`, flags de filtro rígido |

### Saídas

Lista de `EdictMatch` com:

- identificação (`external_id`, `title`, `agency`, `year`, `url`)
- `distance` (operador `<=>` do pgvector)
- `similarity` ≈ `1 - distance` (vetores L2-normalizados)
- `reasons[]` — justificativas legíveis (área, TRL, porte, órgão, score)
- `excerpt` — trecho do texto do edital

### O que ele **não** faz

- Não baixa editais da internet (isso é o **Scraper**, T-005)
- Não gera embeddings em lote (isso é o **Indexer**, T-020) — só embute a *query*
- Não pontua como “banca” completa (isso será o **Scoring**, T-040)
- Não redige o rascunho final (isso é o **Generation**, T-006/T-041)

---

## 2. Por que “busca híbrida”

Há dois tipos de sinal:

1. **Estrutural (SQL):** porte, TRL, área, órgão, ano — regras de elegibilidade cadastradas.
2. **Semântico (vetor):** proximidade de significado entre o texto do projeto e o texto do edital.

Só SQL perde editais bem descritos em prosa.  
Só vetor pode ranquear algo semanticamente próximo mas inelegível.  
O híbrido **filtra** no SQL e **ordena** pelo cosseno.

```text
Empresa + Projeto
        │
        ▼
  embed(query)  ──►  vector(384)
        │
        ▼
  SELECT ... FROM edicts
  WHERE embedding IS NOT NULL
    [AND filtros SQL opcionais]
  ORDER BY embedding <=> query_vector
  LIMIT k
        │
        ▼
  EdictMatch + reasons[]
```

---

## 3. Como foi desenvolvido (decisões técnicas)

### 3.1 Base aproveitada

| Peça já existente | Uso no Retrieval |
|-------------------|------------------|
| Neon + `edicts.embedding vector(384)` | Corpus indexado (T-020) |
| `app/embeddings.py` | Mesmo backend da query (`auto` / MiniLM / hashing) |
| `db/session.py` | Conexão async SQLAlchemy + asyncpg |
| Operador `<=>` | Distância de cosseno do pgvector |

### 3.2 API do agente

Arquivo principal: `agents/retrieval_agent.py`

- `RetrievalAgent.retrieve(project, company, **filters) -> RetrievalResult`
- Helpers:
  - `cosine_similarity_from_distance`
  - `build_reasons` (gera as razões exibidas ao usuário/TCC)

### 3.3 Filtros SQL implementados

Todos são **opcionais** (no MVP muitos editais ainda não têm `min_trl` / `company_sizes` preenchidos):

| Filtro | Comportamento |
|--------|----------------|
| `agency` | `agency ILIKE %valor%` |
| `year` | `year IS NULL OR year = :year` |
| `require_area_overlap` | `edicts.areas && company.areas` (overlap de arrays) |
| `enforce_trl` | `min_trl IS NULL OR min_trl <= company.trl` |
| `enforce_size` | array vazio **ou** porte da empresa ∈ `company_sizes` |

Filtros “soft” (padrão desligado): não zeram o corpus cedo demais enquanto o cadastro de metadados ainda é parcial. As **reasons** ainda alertam inconsistências de TRL/porte quando os dados existem.

### 3.4 Ranking vetorial

1. Monta `query = title + text` do projeto  
2. `embed_text(query)` com o **mesmo** embedder do indexador (importante para o espaço vetorial ser compatível)  
3. `ORDER BY embedding <=> :q`  
4. `similarity = 1 - distance`

> Se o indexador usou `hashing-vectorizer` (fallback Bayer), a query também deve usar hashing — garantido por `get_embedder()` compartilhado.

### 3.5 CLI de demonstração

Arquivo: `scripts/retrieve_edicts.py`

```powershell
# Consulta livre
python -m scripts.retrieve_edicts --query "startup inovacao digital IA" --k 5

# Só FINEP
python -m scripts.retrieve_edicts --query "..." --agency FINEP

# Usa o texto de um edital já no banco como se fosse o projeto (smoke)
python -m scripts.retrieve_edicts --from-edict finep-986129 --k 3
```

Saída JSON padrão: `data/outputs/retrieval_last.json`

### 3.6 Testes

`tests/test_retrieval.py` cobre funções puras (`similarity`, `reasons`) sem depender de rede/Neon.

---

## 4. Como executar (reprodução)

Pré-requisitos: migrate + seed + index (T-010–T-020) já feitos.

```powershell
.\.venv\Scripts\Activate.ps1
$env:EMBEDDING_BACKEND="hashing"   # se HuggingFace estiver bloqueado
python -m scripts.retrieve_edicts --query "startup inovacao tecnologias digitais" --agency FINEP --k 5
```

---

## 5. DoD da T-030

| Critério | Status |
|----------|--------|
| `retrieve(project, company) → list[EdictMatch]` | Implementado |
| Filtros SQL + cosseno | Implementado |
| Razões de adequação | Implementado |
| CLI + documentação | Implementado |
| Smoke no Neon | Ver execução no ambiente do projeto |

---

## 6. Próximo elo do pipeline

```text
Scraper → Indexer → [Retrieval] → Scoring → Generation
                         ▲
                      você está aqui
```
