# Resumo do grupo — SADS (leitura rápida)

**Para ler antes da banca (≤ 4 páginas).**  
Detalhes: `docs/MANUAL_COMPLETO_SADS.md`.

---

## 1. O que é

**SADS** = Sistema de Apoio à Decisão para Fomento à Inovação.  
Recebe empresa + PDF do projeto, cruza com editais (piloto **FINEP**) e devolve **ranking explicável** (score, critérios, lacunas, link da chamada).

Não garante aprovação. Não substitui especialista.

---

## 2. Problema

Oportunidades de fomento existem, mas estão fragmentadas. O custo está em interpretar critérios, comparar e evitar esforço em chamada incompatível.

---

## 3. Fluxo que todo mundo deve saber desenhar

```text
Landing → Cadastro/Login → Upload PDF → Extração/formulário
  → Avaliar → Retrieval → Scoring → Relatório (applications)
```

**Antes / em paralelo (corpus):** Coletor FINEP → Indexador (embeddings) → Neon/pgvector.

---

## 4. O que é agente × o que não é

| Agente (sim) | Não é agente |
|--------------|--------------|
| Coletor, Indexador, Retrieval, Scoring, Generation, Orquestrador | Login, CRUD, upload, tela do relatório, gravar no banco |

Na UI, o botão Avaliar chama Retrieval + Scoring. Generation completa aparece sobretudo no pipeline CLI/`submit-project`.

---

## 5. Stack real

- API: **FastAPI** (`app/`)  
- UI logada: **HTML/CSS/JS** (`web/`)  
- Landing: **Next.js** export (`landing/out`)  
- Banco: **Neon PostgreSQL + pgvector**  
- LLM: **`none` + template** (sem API paga no PoC)  
- Embeddings: sentence-transformers ou **hashing**  

---

## 6. Segurança (falar com honestidade)

- Projeto **não** treina modelo.  
- Projeto **não** entra no corpus público.  
- **Sem LLM externo** no fluxo atual.  
- Isolamento por `company_id` — authz em todas as rotas ainda **parcial**.  
- Não dizer “nunca vaza” / “LGPD 100%”.

---

## 7. Implementado vs planejado

**Implementado:** auth senha, Fase A UI, FINEP, retrieval, scoring v2, relatório, aplicações.  
**Planejado:** SSO, RBAC fino, chat LLM seguro, multi-fonte, AHP/TOPSIS.

---

## 8. Contribuição do TCC

Pipeline multiagente + score explicável + infra de corpus vetorial — não “só a interface”.

---

## 9. Sete frases para decorar

1. Apoio à decisão, humano decide.  
2. Complexidade = agentes orquestrados.  
3. Retrieval híbrido (SQL + cosseno).  
4. Scoring com pesos e gates.  
5. LLM externo off no PoC.  
6. PoC = FINEP, não o Brasil inteiro.  
7. Próximos: SSO, RBAC, chat seguro, validação.
