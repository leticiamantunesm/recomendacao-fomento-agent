# Orchestrator + Generation no pipeline (T-041 / T-042)

## Funcao

O **Orchestrator** encadeia o fluxo E2E do MVP:

```text
ProjectQuery + CompanyProfile
        │
        ▼
 RetrievalAgent  →  matches (SQL + cosseno)
        │
        ▼
 ScoringAgent    →  ScoreReport[] (0–100 + forcas/fraquezas)
        │
        ▼
 GenerationAgent →  rascunho template (+ secao de scoring)
        │
        ▼
 Relatorio Markdown em data/outputs/
```

A API `POST /api/v1/submit-project` expoe o mesmo fluxo.

## Generation (T-041)

- Usa `LLM_PROVIDER=none` → template local (custo zero).
- Apos o template base, anexa secao **7. Avaliacao automatica** com nota, breakdown, forcas e fraquezas.

## Como rodar

### CLI

```powershell
$env:EMBEDDING_BACKEND="hashing"
$env:PYTHONIOENCODING="utf-8"
python -m scripts.run_pipeline --query "startup inovacao digital inteligencia artificial" --agency FINEP --k 5
```

Saidas:
- `data/outputs/pipeline_report_*.md`
- `data/outputs/pipeline_last.json`

### API

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Exemplo de body (`/docs` ou curl):

```json
{
  "project_title": "Plataforma de inovacao digital",
  "project_text": "Projeto de startup EPP com foco em IA e inovacao...",
  "company_name": "Empresa Demo TCC",
  "company_size": "EPP",
  "company_trl": 5,
  "company_areas": ["inovacao", "tecnologias digitais"],
  "agency": "FINEP",
  "k": 5,
  "top_n_drafts": 1
}
```

## Arquivos

| Arquivo | Papel |
|---------|--------|
| `agents/orchestrator.py` | Encadeamento + export do relatorio |
| `agents/generation_agent.py` | Rascunho enriquecido com scoring |
| `app/main.py` | `/health` + `/api/v1/submit-project` |
| `app/schemas.py` | Request/response Pydantic |
| `scripts/run_pipeline.py` | Smoke E2E via CLI |
