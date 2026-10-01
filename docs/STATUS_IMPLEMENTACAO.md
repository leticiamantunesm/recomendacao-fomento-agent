# Status de implementação — SADS

Gerado em 2026-09-30. Classificações alinhadas ao código inspecionado.

| Funcionalidade | Status | Evidência | Pendência | Prioridade |
|----------------|--------|-----------|-----------|------------|
| Landing pública | IMPLEMENTADO | `landing/out`, `app/main.py` `/` | Rebuild Next quando editar | Média |
| Registro org + admin | IMPLEMENTADO | `routes_auth.register`, `register.html` | — | — |
| Login senha + token | IMPLEMENTADO | `auth.py`, `login.html` | SSO | Alta (TCC) |
| Reset senha | PARCIALMENTE IMPLEMENTADO | forgot/reset; SMTP opcional | SMTP prod | Média |
| Dashboard métricas | IMPLEMENTADO | `dashboard.html`, `GET /dashboard` | — | — |
| CRUD empresa | IMPLEMENTADO | `routes_fase_a` companies | — | — |
| Equipe / employees | IMPLEMENTADO | `employee.html` | RBAC UI | Média |
| Papéis (RBAC fino) | PARCIALMENTE IMPLEMENTADO | campo `role` | Enforcement | Alta |
| Upload projeto PDF | IMPLEMENTADO | `POST /projects` | Limite tamanho explícito | Média |
| Extração texto PDF | PARCIALMENTE IMPLEMENTADO | `extract_pdfs`, `pdf_form` | OCR | Alta |
| Formulário projeto | IMPLEMENTADO | `project-new.html` PATCH | — | — |
| Coleta FINEP | IMPLEMENTADO (piloto) | `scraper_agent`, `finep.py` | Robustez prod | Alta |
| Seed / purge FINEP | IMPLEMENTADO | `seed_corpus.py` | — | — |
| Embeddings edicts | IMPLEMENTADO | `indexer_agent`, pgvector | HF vs hashing | Média |
| Retrieval híbrido | IMPLEMENTADO | `retrieval_agent.py` | — | — |
| Scoring matriz v2 | IMPLEMENTADO | `scoring_agent.py` | AHP/TOPSIS | Alta (pesquisa) |
| Evaluate API + UI | IMPLEMENTADO | `evaluate_project`, `project-evaluate` | Authz | Alta |
| URL FINEP no ranking | IMPLEMENTADO | `ApplicationOut.url` | — | — |
| Applications / outcomes | IMPLEMENTADO | `applications.html` | — | — |
| Materiais / documents | IMPLEMENTADO | `materials.html` | UX | Baixa |
| CNPJ lookup | IMPLEMENTADO | BrasilAPI | Disponibilidade API | Baixa |
| Generation template | IMPLEMENTADO | `generation_agent`, `llm.py` | — | — |
| Orchestrator E2E | IMPLEMENTADO | `orchestrator.py`, `submit-project` | — | — |
| Chat LLM | PLANEJADO | `product_ui.md` Fase B | Desenho seguro | Alta (TCC) |
| SSO / OAuth | PLANEJADO | README Fase B | — | Alta |
| Authz em todas rotas projeto | PARCIALMENTE IMPLEMENTADO | só auth router usa Depends | Hardening | **Crítica** |
| Multi-fonte editais | PLANEJADO | README OUT | FAPESP/BNDES… | Alta |
| AHP | PLANEJADO | proposta TCC/slides | — | Média |
| TOPSIS | PLANEJADO | proposta | — | Média |
| LangChain/CrewAI | NÃO IDENTIFICADO no runtime | README “opcional” | Não depende | — |
| Testes unitários núcleo | IMPLEMENTADO | `tests/` (~10) | E2E authz | Alta |
| Política LGPD publicada | PARCIAL / PLANEJADO | copy landing | Documento formal | Média |
| Tema claro/escuro UI | IMPLEMENTADO | `web/app.js` `rf_theme` | — | Baixa |

---

## Legenda rápida para a banca

- **Verde (IMPLEMENTADO):** pode demonstrar.  
- **Amarelo (PARCIAL):** existe com ressalvas — diga a ressalva.  
- **Azul (PLANEJADO):** roadmap TCC — não vender como pronto.
