# Frontend — guia técnico (Fase A)

Complementa [`product_ui.md`](product_ui.md) (visão de produto).

## Como subir

```powershell
$env:EMBEDDING_BACKEND="hashing"
$env:PYTHONIOENCODING="utf-8"
python -m scripts.migrate_db
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abrir: http://127.0.0.1:8000/

Fluxo demo: **Empresa → Funcionário → Início → Novo projeto → Avaliação top 3 → Aplicações**.

## Arquitetura

```text
Browser (web/*.html + /static)
    │  same-origin fetch
    ▼
FastAPI (app/main.py)
    ├── StaticFiles → web/
    ├── app/routes_fase_a.py  (/api/v1/...)
    └── Orchestrator / Scoring / Retrieval → Neon
```

## Paginas

| Arquivo | Tela |
|---------|------|
| `web/index.html` | 3 — home + dash |
| `web/company.html` | 1 — empresa |
| `web/employee.html` | 2 — funcionário |
| `web/project-new.html` | 4 — upload + form |
| `web/project-evaluate.html` | 4 — relatório (wireframe) |
| `web/materials.html` | 6 — repositório |
| `web/applications.html` | 7 — outcomes |
| Chat | placeholder na nav (Fase B) |

Sessão demo: `localStorage` (`rf_company_id`, `rf_employee_id`, …).

## APIs Fase A

| Método | Rota |
|--------|------|
| CRUD | `/api/v1/companies` |
| CRUD | `/api/v1/employees?company_id=` |
| POST multipart | `/api/v1/projects` |
| PATCH/GET | `/api/v1/projects/{id}` |
| POST | `/api/v1/projects/{id}/evaluate` |
| GET/POST | `/api/v1/documents` |
| GET/PATCH | `/api/v1/applications` |
| GET | `/api/v1/dashboard?company_id=` |

Schema SQL: [`db/init/03_fase_a.sql`](../db/init/03_fase_a.sql).

## Status

| Item | Status |
|------|--------|
| Documentação 7 telas A/B | Feito |
| Schema employees/documents/applications | Feito |
| APIs Fase A | Feito |
| Páginas web/* | Feito |
| Chat / SSO | Fase B |

## O que NAO vai ao browser

`DATABASE_URL`, senhas, chaves LLM.
