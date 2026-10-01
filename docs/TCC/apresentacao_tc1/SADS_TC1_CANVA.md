# SADS — TC1 · Roteiro para Canva

Uso: copiar bloco a bloco para o Canva. Pouco texto, 1 mensagem por slide.  
Tempo total: ~10 min · 9 slides · ~50–70 s/slide (abertura/encerramento mais curtos).

Identidade: fundo navy · destaque ciano · texto branco/cinza-azulado · logo SADS.

---

## SLIDE 1 — Abertura (~30 s)

**Título:** SADS  
**Subtítulo:** Sistema de Apoio à Decisão para Fomento à Inovação

**Posicionamento (1 linha):**  
Plataforma para conectar projetos de inovação aos mecanismos de fomento mais aderentes.

**Rodapé:**
- TC1 · Ciência da Computação · UNIP Paraíso · 2026
- Letícia Melo · Filipe Ribeiro · Fabiano Rocha · Ruben Pereira · Victor Yukio

**Fala:** apresentar o grupo e o propósito em uma frase.

---

## SLIDE 2 — Contexto (~60 s)

**Título:** Inovar exige investimento e acesso aos mecanismos certos

**Diagrama (horizontal):**
```text
Projeto de inovação  →  Instituições (FINEP, FAPESP, BNDES, EMBRAPII…)
                     →  Mecanismos (editais, subvenção, crédito, fiscais, ICTs)
                     →  Critérios e processos distintos
```

**Mensagem:**  
O problema não é só falta de recurso — é identificar e acessar o mecanismo adequado.

**Canva:** 4 caixas + setas. Sem lista longa de programas.

---

## SLIDE 3 — Problema (~70 s)

**Título:** Encontrar o mecanismo adequado ainda é um processo complexo

**Dores (máx. 6 chips):**
- Fragmentação das informações
- Desconhecimento das oportunidades
- Critérios de elegibilidade complexos
- Dificuldade de comparar programas
- Alto esforço para interpretar editais
- Dependência de especialistas

**Jornada atual (marcar atritos):**
```text
Buscar → Ler editais → Interpretar → Comparar → Adaptar projeto → Submeter
```

**Mensagem:**  
Decisão manual, fragmentada, demorada e dependente de conhecimento especializado.

**Nota (opcional, pequenina):**  
Referência no material do projeto (SADS.pdf): consultorias R$ 1–5 mil / análise; êxito 0,5–2% (até 3–5%). Não é estatística conclusiva.

---

## SLIDE 4 — Questão e objetivo (~60 s)

**Título:** Como apoiar uma decisão mais rápida, consistente e explicável?

**Questão norteadora:**  
Como utilizar dados e inteligência artificial para recomendar mecanismos de fomento compatíveis com o perfil da empresa e do projeto?

**Objetivo geral:**  
Desenvolver um sistema de apoio à decisão que analise empresa/projeto, compare critérios e gere recomendações classificadas e explicáveis.

**Objetivos específicos (3):**
1. Estruturar informações (empresa, projeto, programas)
2. Avaliar elegibilidade e aderência
3. Apresentar ranking, justificativas e lacunas

**Mensagem:**  
O SADS **não substitui** a decisão humana — organiza informação e apoia a decisão.

---

## SLIDE 5 — Solução (~70 s)

**Título:** SADS — recomendação inteligente e explicável

**O quê:** SaaS multi-tenant que recebe perfil + PDF do projeto e devolve ranking explicável.

**Fluxo:**
```text
Empresa + Projeto
  → Extração e estruturação
  → Regras / critérios + corpus de programas
  → Motor de recomendação (agentes)
  → Ranking + relatório (score, lacunas, plano)
```

**Benefícios (5 chips curtos):**
- Centralização
- Menos esforço de busca
- Recomendação personalizada
- Transparência (score explicável)
- Apoio ao planejamento da submissão

---

## SLIDE 6 — Protótipo (~90 s)

**Título:** Da submissão do projeto à recomendação

**Jornada (mockups / prints):**
1. Landing / acesso
2. Cadastro da organização
3. Login
4. Upload do PDF
5. Avaliação
6. Ranking + relatório (destaque)
7. Link para a página oficial do edital (FINEP)

**Já no PoC:** landing, auth, upload, corpus FINEP, scoring, relatório, links FINEP.  
**Visão futura:** marcar visualmente (SSO, chat, multi-fonte contínua).

**Valor do relatório:** ranking · score · critérios · lacunas · plano de ação · link oficial.

**Canva:** faixa horizontal de telas; destacar o relatório.

---

## SLIDE 7 — Agentes, orquestração e infraestrutura ⭐ (~90 s)

**Título:** A complexidade está no pipeline de agentes

**Mensagem:**  
Não é um chatbot. É um sistema multiagente com contratos claros, orquestração e infraestrutura de dados.

### Diagrama principal (copiar para Canva)

```text
┌─────────────┐   ┌─────────────┐   ┌──────────────┐
│  1. Coletor │ → │ 2. Indexador│ → │ Corpus Neon  │
│  (Scraper)  │   │ (Embeddings)│   │ + pgvector   │
└─────────────┘   └─────────────┘   └──────┬───────┘
                                           │
     PDF do projeto + perfil da empresa     │
                    │                      │
                    ▼                      ▼
            ┌───────────────┐     ┌────────────────┐
            │ 3. Retrieval  │ ←── │ Editais FINEP  │
            │ SQL + cosseno │     │ indexados      │
            └───────┬───────┘     └────────────────┘
                    ▼
            ┌───────────────┐
            │ 4. Scoring    │  matriz v2 + gates
            │ (0–100)       │
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │ 5. Generation │  template local
            │ (rascunho)    │  LLM_PROVIDER=none
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │ Orquestrador  │  + API / UI
            │ Relatório MD  │  applications
            └───────────────┘
```

### Papel de cada agente (caixa curta no slide ou nota)

| Agente | Entrada | Saída | Função |
|--------|---------|-------|--------|
| **Coletor** | API FINEP | PDFs + metadados | Atualizar corpus de chamadas |
| **Indexador** | Texto do edital | Vetor (embedding) | Indexar para busca semântica |
| **Retrieval** | Projeto + perfil | Top-k candidatos | Busca híbrida (filtros SQL + similaridade) |
| **Scoring** | Candidatos | Score + breakdown + lacunas | Decisão multicritério explicável |
| **Generation** | Score + trechos | Rascunho estruturado | Apoio documental **sem LLM externo** |
| **Orquestrador** | Request E2E | Relatório + JSON | Encadear o pipeline |

### Matriz de scoring (mini-bloco)

```text
score = 0,30·sim + 0,25·tema + 0,15·TRL + 0,15·porte + 0,10·região + 0,05·orçamento
```

Gates: prazo encerrado, porte/TRL/região incompatíveis → penalização / inelegível.

### Infraestrutura (1 linha no slide)

PostgreSQL (Neon) + pgvector · FastAPI · UI autenticada · projetos **isolados** do corpus público.

### PoC vs proposta (1 linha)

PoC: FastAPI + auth senha + FINEP.  
Proposta TCC: convergência UI/API, SSO, multi-fonte, métodos multicritério avançados (AHP/TOPSIS a validar).

**Fala-chave:**  
A contribuição acadêmica está na **decomposição em agentes**, na **orquestração** e na **infraestrutura de corpus + vetores + score auditável**.

---

## SLIDE 8 — Segurança, dados e diferenciais (~60 s)

**Título:** Uma recomendação útil precisa ser confiável

### Três colunas

**Diferenciais**
- Ranking personalizado e explicável
- Visão unificada (começando por FINEP)
- Lacunas + plano de ação
- Isolamento lógico multi-tenant

**Dados dos projetos (PoC)**
- **Sem LLM generativo externo** no fluxo atual
- Texto do projeto **não treina** modelo
- Projeto **não entra** no corpus público de editais
- Uso só em tempo de análise (extração + similaridade + score)
- Embeddings = NLP de similaridade (não é chatbot)

**Limitações (maturidade)**
- Qualidade depende do catálogo atualizado
- Regras/metadados exigem validação
- Recomendação **não garante** aprovação
- Apoia gestores — não substitui especialistas
- Auth/RBAC ainda em evolução no TCC

**Frase de segurança (rodapé do slide):**  
“No PoC: análise local + corpus de editais; sem envio a APIs de LLM. Chat com LLM, se vier, será com controle explícito de dados.”

---

## SLIDE 9 — Próximos passos e encerramento (~50 s)

**Título:** Próximos passos para o TCC

### Linha do tempo (chips)

1. Refinar requisitos e papéis de usuário  
2. Consolidar modelo de dados  
3. Coleta multi-fonte + atualização contínua  
4. Evoluir motor (AHP/TOPSIS a validar; regras)  
5. SSO + permissões por perfil  
6. Chat assistido (Fase B) com proteção de dados  
7. Validação com usuários + testes de segurança  
8. Documentar resultados e limitações  

### Melhorias previstas (destaque — cards)

| Tema | O que entregar | Como manter dados seguros |
|------|----------------|---------------------------|
| **SSO / OAuth 2.0** | Login corporativo (Google/Microsoft/IdP) | Identidade institucional; menos senhas locais; sessão auditável |
| **Permissões por perfil (RBAC)** | Admin, analista, consultor, somente leitura | Cada papel vê/edita só o necessário (minimização LGPD) |
| **Chat com LLM** | Perguntas sobre o projeto/edital e apoio a texto | Preferir **Ollama local** ou API com **retenção zero / DPA**; enviar só trechos necessários; **opt-in**; log de finalidade; projeto **nunca** usado para treino do provedor (contrato) |
| **Catálogo multi-fonte** | FAPESP, BNDES, EMBRAPII… além de FINEP | Corpus público separado dos PDFs privados da empresa |
| **Hardening de API** | Auth obrigatória em todas as rotas de projeto | Impede acesso cruzado entre tenants |
| **Validação empírica** | Testes com usuários reais | Medir se o ranking é compreensível e útil (**a validar**) |
| **AHP / TOPSIS** | Pesos e ranking multicritério formal | Métodos clássicos + regras; LLM só auxiliar, se houver |

### Critérios de sucesso do TCC
- Identifica programas elegíveis  
- Gera ranking justificável  
- Usuário entende o “porquê”  
- Detecta informações ausentes  
- Fluxo ponta a ponta concluível  

**Fechamento:**  
O SADS transforma informações fragmentadas em decisão estruturada, explicável e orientada ao projeto.

**Obrigado — perguntas.**

---

## Roteiro oral (resumo ~820 palavras — usar nas notas do Canva)

1. **Abertura:** SADS conecta projeto ↔ fomento aderente.  
2. **Contexto:** oportunidades existem, mas dispersas.  
3. **Problema:** jornada manual e cara em tempo/conhecimento.  
4. **Objetivo:** SAD explicável; humano decide.  
5. **Solução:** PDF + perfil → motor → ranking.  
6. **Protótipo:** mostrar fluxo e relatório (valor central).  
7. **Agentes:** coletor→índice→retrieval→scoring→generation; orquestrador; Neon/pgvector; score com pesos e gates. Complexidade = pipeline, não “só UI”.  
8. **Segurança:** sem LLM externo no PoC; sem treino com projetos; limitações honestas.  
9. **Próximos:** SSO, RBAC, chat seguro, multi-fonte, hardening, validação.

---

## O que NÃO inventar na fala

- Métricas de acerto sem validação  
- “LGPD 100% concluída”  
- “SSO já pronto”  
- “LLM decide o edital”  
- Confundir PoC FINEP com catálogo nacional completo  

---

## Assets sugeridos no Canva

- Logo: `assets/sads-logo.png`
- Prints: landing, register, login, upload, relatório real, dashboard  
- Diagrama de agentes (Slide 7) — prioridade visual #1  
- Ícones mínimos: fluxo, escudo, pipeline  

---

## Tempo

| # | Slide | s |
|---|--------|--:|
| 1 | Abertura | 30 |
| 2 | Contexto | 60 |
| 3 | Problema | 70 |
| 4 | Questão/objetivo | 60 |
| 5 | Solução | 70 |
| 6 | Protótipo | 90 |
| 7 | Agentes / infra | 90 |
| 8 | Segurança / diferenciais | 60 |
| 9 | Próximos passos | 50 |
| | **Total** | **≈ 9 min 40 s** |
