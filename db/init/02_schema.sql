-- Schema inicial (S1 / T-010–T-012)
-- Neon: aplicado via `python -m scripts.migrate_db`
-- Requer: CREATE EXTENSION vector; (01_extensions.sql)

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS companies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    size            TEXT,
    trl             INTEGER,
    areas           TEXT[] NOT NULL DEFAULT '{}',
    cnpj            TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    file_path       TEXT,
    raw_text        TEXT,
    embedding       vector(384),
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS edicts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id     TEXT UNIQUE,
    source          TEXT,
    title           TEXT NOT NULL,
    agency          TEXT,
    year            INTEGER,
    areas           TEXT[] NOT NULL DEFAULT '{}',
    min_trl         INTEGER,
    company_sizes   TEXT[] NOT NULL DEFAULT '{}',
    raw_text        TEXT,
    embedding       vector(384),
    file_path       TEXT,
    url             TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_edicts_external_id ON edicts (external_id);
CREATE INDEX IF NOT EXISTS idx_edicts_agency ON edicts (agency);
CREATE INDEX IF NOT EXISTS idx_edicts_year ON edicts (year);
CREATE INDEX IF NOT EXISTS idx_projects_company_id ON projects (company_id);

-- Índice vetorial: criar após popular embeddings (T-020+).
-- Exemplo (cosine):
-- CREATE INDEX IF NOT EXISTS idx_edicts_embedding_cosine
--   ON edicts USING hnsw (embedding vector_cosine_ops);
