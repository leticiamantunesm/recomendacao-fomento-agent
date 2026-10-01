# Perguntas e respostas — TC1 SADS

Respostas curtas e alinhadas ao código. Detalhe: `docs/MANUAL_COMPLETO_SADS.md`.

Sugestão de responsável (adaptar ao grupo):  
**A** contexto · **B** UX/protótipo · **C** arquitetura · **D** motor · **E** segurança/próximos.

| # | Pergunta | Resposta sugerida | Resp. |
|---|----------|-------------------|-------|
| 1 | Qual é o problema de pesquisa? | Como apoiar de forma estruturada e explicável a identificação de mecanismos de fomento compatíveis com empresa e projeto. | A |
| 2 | Qual a contribuição acadêmica? | Pipeline de componentes especializados (coleta→índice→retrieval→scoring), ranking explicável e separação corpus/projeto — não só UI. | A/D |
| 3 | Por que é um SAD? | Organiza alternativas e justificativas; a decisão final é humana. | A |
| 4 | Por que AHP? | Está na **proposta** para pesos; **ainda não implementado**. Hoje usamos pesos fixos da matriz v2. | D |
| 5 | Por que TOPSIS? | Planejado para ranking multicritério formal; **não está no código** do scoring atual. | D |
| 6 | Como os pesos são definidos? | Constantes em `SCORE_WEIGHTS`: sim 30%, área 25%, TRL 15%, porte 15%, região 10%, orçamento 5%. | D |
| 7 | Como avaliar qualidade do ranking? | Comparação com especialista, compreensão das justificativas, outcomes em `applications` — **a validar** com usuários. | E |
| 8 | Critérios eliminatórios? | Gates no scoring (prazo, porte, TRL, região) + filtros SQL no retrieval. | D |
| 9 | Como evitar recomendações incorretas? | Gates, breakdown explícito, revisão humana, corpus atualizado; score não é garantia. | D/E |
| 10 | E se faltam informações? | Extração fraca → formulário manual; metadados ausentes → nota neutra ~70 no critério. | D/B |
| 11 | Como os agentes foram estruturados? | Módulos Python em `agents/` com contratos dataclass, orquestrados por `Orchestrator` ou pela rota evaluate. | C/D |
| 12 | Foi treinado algum modelo? | **Não.** | D |
| 13 | Usa modelo pronto? | Embeddings: sentence-transformers (ou hashing). LLM de geração: **desligado** (template). | D |
| 14 | O que está implementado? | Auth senha, UI Fase A, FINEP, retrieval, scoring, relatório, aplicações, landing. | C |
| 15 | O que é protótipo/parcial? | Authz server-side, OCR, metadados FINEP, multi-fonte, chat, SSO. | C/E |
| 16 | Como atualiza a base de programas? | `scripts/refresh_finep_corpus` / coletor FINEP + seed + index. | C |
| 17 | Dados confidenciais? | Projeto por `company_id`, não vai ao corpus; sem LLM externo no PoC. | E |
| 18 | Como funciona multi-tenant? | Tabelas com `company_id`; sessão guarda a empresa. | C |
| 19 | LGPD? | Finalidade/minimização na arquitetura; política formal e direitos do titular ainda em evolução. | E |
| 20 | PDF malicioso / prompt injection? | Risco conhecido: texto entra no retrieval; mitigação futura (limites/sanitização). Hoje confiança no upload autenticado. | E |
| 21 | Por que não só um chatbot? | Chatbot não aplica gates nem ranking auditável; nosso núcleo é retrieval híbrido + scoring. | D |
| 22 | Substitui consultoria? | **Não.** Reduz esforço inicial; especialista e regras oficiais prevalecem. | A |
| 23 | Como provar utilidade? | Demo do fluxo + outcomes + estudo com usuários no TCC (**a validar**). | E |
| 24 | Limitações atuais? | Catálogo FINEP-only, metadados, authz parcial, sem chat/SSO, sem AHP/TOPSIS. | E |
| 25 | O que cada um sabe explicar? | Todos: problema, fluxo, limites. Especialidades A–E acima. | Todos |
| 26 | Qual banco? | Neon PostgreSQL com pgvector. | C |
| 27 | Qual framework da API? | FastAPI. | C |
| 28 | Frontend é React? | Landing sim (Next). Área logada: HTML/JS estático. | B/C |
| 29 | Generation usa GPT? | Não no PoC; `LLM_PROVIDER=none`. | D |
| 30 | Link FINEP no relatório? | Sim, via `edicts.url` / fallback `finep-{id}`. | B |

---

## Se não souber a resposta

1. Admitir o limite.  
2. Apontar o módulo (`agents/…`, `app/…`).  
3. Classificar: implementado / parcial / planejado.  
4. Não inventar.
