# Indexador / embeddings (T-020)

## Objetivo

Transformar `edicts.raw_text` em vetores (`sentence-transformers`) e gravar em `edicts.embedding` (`vector(384)`), com busca por distância de cosseno (`<=>`).

## Modelo

| Item | Valor |
|------|--------|
| Preferido | `sentence-transformers/all-MiniLM-L6-v2` (dim **384**) |
| Fallback | `HashingVectorizer` → 384 dims (**offline**, sem HuggingFace) |
| Env | `EMBEDDING_BACKEND=auto` \| `sentence-transformers` \| `hashing` |
| Textos longos | chunk + média + renormalização L2 |

> No PC Bayer, o download do HuggingFace pode falhar (proxy/SSL). Com `auto`, o sistema cai no hashing automaticamente. No PC pessoal com internet livre, use MiniLM.

## Como rodar

```powershell
.\.venv\Scripts\Activate.ps1
python -m scripts.index_edicts
python -m scripts.index_edicts --smoke "startup inovacao digital"
```

| Flag | Efeito |
|------|--------|
| `--reindex` | Recalcula mesmo se já houver embedding |
| `--limit N` | Processa só N registros |
| `--smoke "..."` | Top-k por cosseno após indexar |
| `--k N` | Tamanho do ranking no smoke |

## Código

- `app/embeddings.py` — encode / chunk / literal pgvector  
- `agents/indexer_agent.py` — UPDATE no Neon + índice HNSW cosine  
- `scripts/index_edicts.py` — CLI  

## SQL de checagem (Neon)

```sql
SELECT external_id, title,
       (embedding IS NOT NULL) AS has_embedding
FROM edicts
ORDER BY external_id;

-- top-3 similaridade (exemplo: substitua o vetor após gerar um query embedding)
-- SELECT external_id, title, embedding <=> '[...]'::vector AS distance
-- FROM edicts WHERE embedding IS NOT NULL
-- ORDER BY distance LIMIT 3;
```

## DoD (T-020)

- [x] `indexer_agent` gera embeddings  
- [x] `edicts.embedding` preenchido (NOT NULL)  
- [x] índice cosine (`idx_edicts_embedding_cosine`)  
- [x] smoke de similaridade via CLI  
