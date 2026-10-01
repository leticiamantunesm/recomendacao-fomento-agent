# Migrações e seed (S1 / T-010–T-014)

## Pré-requisitos

1. Neon com extensão `vector` (já feita no SQL Editor)
2. Arquivo `.env` com `DATABASE_URL` real:

```powershell
copy .env.example .env
# edite e cole a connection string do Neon (Show password)
```

3. Corpus coletado/extraído:

```powershell
python -m scripts.collect_editais --source finep --limit 5 --extract
```

---

## 1. Aplicar schema

```powershell
.\.venv\Scripts\Activate.ps1
python -m scripts.migrate_db
```

Cria/atualiza:

- `companies`
- `projects`
- `edicts` (com coluna `embedding vector(384)` ainda vazia)
- índices básicos

Scripts SQL: `db/init/01_extensions.sql`, `db/init/02_schema.sql`

---

## 2. Seed do corpus

```powershell
python -m scripts.seed_corpus
```

- Lê `data/corpus_manifest.csv`
- Associa textos em `data/texts/`
- Faz upsert em `edicts` por `external_id` (ex.: `finep-1019381`)
- Cria empresa demo `Empresa Demo TCC`

Embeddings **não** são gerados aqui (tarefa do Indexer — T-020).

---

## Conferir no Neon

SQL Editor:

```sql
SELECT external_id, agency, year, length(raw_text) AS chars
FROM edicts
ORDER BY created_at DESC;
```

---

## Arquivos

| Arquivo | Papel |
|---------|-------|
| `db/init/02_schema.sql` | DDL |
| `db/models.py` | ORM |
| `db/session.py` | Engine async Neon |
| `scripts/migrate_db.py` | Aplica SQL |
| `scripts/seed_corpus.py` | Carga corpus |
