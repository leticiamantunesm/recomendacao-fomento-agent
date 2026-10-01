-- Fase A UI: enriquecer companies + employees + documents + applications
-- Idempotente (ADD COLUMN IF NOT EXISTS / CREATE TABLE IF NOT EXISTS)

ALTER TABLE companies ADD COLUMN IF NOT EXISTS trade_name TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS employee_count INTEGER;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS revenue_brl NUMERIC(18, 2);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS uf TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS cnae TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE projects ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'draft';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS form_data JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS employees (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL,
    area            TEXT,
    role_title      TEXT,
    phone           TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, email)
);

CREATE INDEX IF NOT EXISTS idx_employees_company_id ON employees (company_id);

CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    project_id      UUID REFERENCES projects(id) ON DELETE SET NULL,
    filename        TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    doc_type        TEXT NOT NULL DEFAULT 'other',
    content_type    TEXT,
    byte_size       INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_company_id ON documents (company_id);
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents (project_id);

CREATE TABLE IF NOT EXISTS applications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    edict_id        UUID REFERENCES edicts(id) ON DELETE SET NULL,
    edict_external_id TEXT,
    edict_title     TEXT,
    rank_position   INTEGER,
    score           DOUBLE PRECISION,
    breakdown       JSONB NOT NULL DEFAULT '{}'::jsonb,
    strengths       TEXT[] NOT NULL DEFAULT '{}',
    weaknesses      TEXT[] NOT NULL DEFAULT '{}',
    summary         TEXT,
    status          TEXT NOT NULL DEFAULT 'recommended',
    approved_amount_brl NUMERIC(18, 2),
    outcome_notes   TEXT,
    was_in_top3     BOOLEAN,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_applications_company_id ON applications (company_id);
CREATE INDEX IF NOT EXISTS idx_applications_project_id ON applications (project_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications (status);
