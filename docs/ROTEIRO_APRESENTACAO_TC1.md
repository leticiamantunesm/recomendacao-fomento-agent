# Roteiro de apresentação TC1 — SADS

**Duração total:** ≈ 9 min 40 s · **9 slides** · Canva (identidade navy + ciano).  
Base: `docs/TCC/apresentacao_tc1/SADS_TC1_CANVA.md` · Manual: `docs/MANUAL_COMPLETO_SADS.md`.

---

## Slide 1 — Abertura (30 s)

| | |
|--|--|
| **Objetivo** | Apresentar tema e grupo |
| **Visual** | Logo · SADS · subtítulo · nomes · TC1 UNIP |
| **Mensagem** | Conectar projetos aos mecanismos de fomento mais aderentes |
| **Fala** | “Apresentamos o SADS, sistema de apoio à decisão para fomento à inovação…” |
| **Transição** | “Começamos pelo contexto do fomento no Brasil.” |
| **Perguntas** | O que significa a sigla? |

---

## Slide 2 — Contexto (60 s)

| | |
|--|--|
| **Objetivo** | Mostrar ecossistema disperso |
| **Visual** | Projeto → instituições → mecanismos → critérios |
| **Mensagem** | Não falta só recurso; falta achar o mecanismo certo |
| **Fala** | “Existem FINEP, FAPESP, BNDES, EMBRAPII… com regras distintas.” |
| **Transição** | “Na prática, isso vira um problema operacional.” |

---

## Slide 3 — Problema (70 s)

| | |
|--|--|
| **Objetivo** | Dores + jornada com atrito |
| **Visual** | Chips de dores + Buscar→…→Submeter |
| **Mensagem** | Decisão manual, fragmentada, especializada |
| **Fala** | “A dificuldade não é só achar o PDF do edital; é interpretar e comparar.” |
| **Transição** | “Daí a questão do nosso trabalho.” |

---

## Slide 4 — Questão e objetivos (60 s)

| | |
|--|--|
| **Objetivo** | Problema de pesquisa + metas |
| **Visual** | Questão · objetivo geral · 3 específicos |
| **Mensagem** | SAD explicável; humano decide |
| **Fala** | “Como apoiar de forma estruturada e explicável a identificação de mecanismos compatíveis?” |
| **Transição** | “A resposta é o SADS.” |

---

## Slide 5 — Solução (70 s)

| | |
|--|--|
| **Objetivo** | Visão do produto |
| **Visual** | Fluxo Empresa+Projeto → motor → ranking |
| **Mensagem** | SaaS multi-tenant com ranking e lacunas |
| **Fala** | “Recebemos perfil e PDF, aplicamos critérios e devolvemos ranking com justificativas.” |
| **Transição** | “Isso já aparece no protótipo.” |

---

## Slide 6 — Protótipo (90 s)

| | |
|--|--|
| **Objetivo** | Mostrar jornada real |
| **Visual** | Prints: login → upload → relatório (+ link FINEP) |
| **Mensagem** | Valor = relatório explicável |
| **Fala** | “Do cadastro ao relatório: o usuário vê score, critérios, lacunas e a chamada oficial.” |
| **Transição** | “Por baixo, a complexidade está nos agentes.” |
| **Cuidado** | Separar PoC vs futuro (SSO/chat). |

---

## Slide 7 — Agentes / arquitetura (90 s) ⭐

| | |
|--|--|
| **Objetivo** | Valorizar contribuição técnica |
| **Visual** | Faixa A corpus · Faixa B usuário · legenda AGENTE vs NÃO AGENTE |
| **Mensagem** | Não é chatbot; é pipeline orquestrado |
| **Fala** | “Coletor e indexador preparam FINEP. No evaluate, Retrieval busca e Scoring ranqueia com pesos e gates. A UI só apresenta.” |
| **Transição** | “Isso também importa para segurança dos dados.” |

---

## Slide 8 — Segurança e limitações (60 s)

| | |
|--|--|
| **Objetivo** | Confiança + maturidade |
| **Visual** | 3 colunas: diferenciais · dados · limites |
| **Mensagem** | Sem LLM externo no PoC; projeto não treina nem vira corpus |
| **Fala** | “Dados do projeto ficam na organização, usados só na análise. Limitações: catálogo, authz a evoluir, não garante aprovação.” |
| **Transição** | “Para o TCC, estes são os próximos passos.” |

---

## Slide 9 — Próximos passos (50 s)

| | |
|--|--|
| **Objetivo** | Viabilidade TCC |
| **Visual** | Timeline + cards SSO / RBAC / chat seguro / multi-fonte |
| **Mensagem** | Roadmap claro, sem overclaim |
| **Fala** | Encerramento sugerido na seção 25 do manual |
| **Fecho** | Obrigado · perguntas |

---

## Regras de fala

- Não ler slide.  
- Não dizer que IA “decide” ou “garante aprovação”.  
- Não apresentar SSO/chat/AHP como prontos.  
- Se travar a demo: explicar o fluxo com o diagrama do slide 7.
