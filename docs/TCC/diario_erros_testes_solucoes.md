# Diário técnico: erros, testes e soluções

**Projeto:** Sistema de Agentes de IA para Gestão e Subvenção de Editais  
**Finalidade:** material de apoio ao TCC (metodologia, implementação, avaliação e lições aprendidas)  
**Atualizado em:** 30/09/2026  

Este documento registra problemas reais encontrados no desenvolvimento do protótipo, como foram diagnosticados, quais testes cobrem (ou ainda não cobrem) cada caso e quais soluções foram adotadas. Serve como base para capítulos de **Materiais e Métodos**, **Resultados e Discussão** e **Limitações**.

---

## 1. Como usar este material no TCC

| Seção do TC (modelo UNIP) | Uso sugerido deste diário |
|---------------------------|---------------------------|
| Introdução / justificativa | Motivação: falhas de elegibilidade e ranking “só por similaridade” não substituem consultoria |
| Fundamentação | Decisões técnicas (Neon+pgvector, embeddings offline, scoring híbrido) |
| Metodologia | Pipeline de agentes, corpus FINEP, matriz de pesos, suíte de testes |
| Implementação | Tabela de incidentes (seção 2) como evidência de engenharia iterativa |
| Avaliação | Resultados de testes + reload FINEP (31 chamadas abertas) + comparação com IAs ([`comparacao_ias_semente_viva.md`](comparacao_ias_semente_viva.md)) |
| Conclusão / trabalhos futuros | Lacunas da seção 5 |

**Princípio metodológico observado:** cada falha de produção/demo gerou (1) hipótese, (2) correção mínima, (3) teste automatizado ou checklist manual, (4) registro aqui.

---

## 2. Catálogo de erros e soluções

Formato de cada item: **contexto → sintoma → causa → solução → evidência/teste → lição para o TCC**.

### 2.1 Ambiente e infraestrutura

#### E01 — PowerShell não aceita heredoc bash

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Geração do plano de sprints / scripts multi-linha no Windows |
| **Sintoma** | Comandos `python << 'EOF'` falham no PowerShell |
| **Causa** | Sintaxe de shell Unix; PowerShell usa outro modelo de redirecionamento |
| **Solução** | Gravar script `.py` temporário e executá-lo; depois remover se for one-shot |
| **Lição** | Documentar *tooling* Windows no TCC (reprodutibilidade do ambiente corporativo) |

#### E02 — Dualidade PC Bayer × PC pessoal (Docker)

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Código no OneDrive/Bayer; Docker só no PC pessoal |
| **Sintoma** | “O banco não sobe” / dúvida se os PCs precisam estar na mesma rede |
| **Causa** | Runtime ≠ editor; Docker é local à máquina onde está instalado |
| **Solução** | (1) Checklist `docs/checklist_pc_pessoal.md`; (2) migração do banco para **Neon** (nuvem + pgvector), eliminando Docker como dependência crítica |
| **Lição** | Arquitetura *cloud-first* aumenta reprodutibilidade acadêmica e reduz atrito corporativo |

#### E03 — Proxy/SSL corporativo bloqueia Hugging Face e APIs externas

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Embeddings `sentence-transformers` / download de modelos; consulta CNPJ (BrasilAPI) |
| **Sintoma** | Timeout SSL, falha de download HF, `CERTIFICATE_VERIFY_FAILED` |
| **Causa** | Rede corporativa intercepta TLS / bloqueia hosts externos |
| **Solução** | `EMBEDDING_BACKEND=hashing` (HashingVectorizer offline, dim 384); CNPJ com retry `verify=True` → `verify=False` controlado; LLM default `none` + template |
| **Teste** | `tests/test_embeddings.py`, `tests/test_llm.py` |
| **Lição** | Fallback offline é requisito de *deploy* em ambiente real, não “atalho” |

#### E04 — Python 3.13/3.14 e pacotes ML

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Setup do venv |
| **Sintoma** | Instalação de dependências ML instável |
| **Causa** | Wheels / suporte ainda irregular em versões muito novas |
| **Solução** | README recomenda Python **3.10–3.12**; hashing evita dependência pesada no demo |
| **Lição** | Fixar versão no capítulo de materiais e métodos |

#### E05 — `ExecutionPolicy` impede ativar venv no PowerShell

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | `Activate.ps1` bloqueado |
| **Solução** | Chamar o interpretador direto: `.\.venv\Scripts\python.exe -m uvicorn ...` |
| **Lição** | Comandos “à prova de política” no README |

#### E06 — Push GitHub “repository not found”

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | `git push` falha com repo inexistente / sem permissão |
| **Causa** | URL remota incorreta, repo ainda não criado ou autenticação sem token |
| **Solução** | Criar repo vazio no GitHub (sem README), conferir `git remote -v`, PAT/login |
| **Lição** | Controle de versão e *remote* fazem parte do processo, não só do código |

---

### 2.2 Corpus e coleta FINEP

#### E07 — Escopo “oportunidades” vs regra “Aberta”

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Fonte FINEP via API Liferay `/o/c/chamadapublicas` |
| **Sintoma** | Edição de editais encerrados / ruído no ranking |
| **Causa** | Sem filtro consistente de situação |
| **Solução** | Filtro `_matches_situacao(..., "aberta")` com `name.lower().startswith("abert")`; CLI `--situacao aberta|todas|encerrada` |
| **Teste** | `tests/test_finep_source.py` |
| **Lição** | Elegibilidade temporal é *gate*, não critério cosmético |

#### E08 — Limite artificial `--limit 15/20` truncava o universo

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Corpus “incompleto” mesmo com reload |
| **Causa** | Default de desenvolvimento tratado como produção |
| **Solução** | `limit=None` / `--all`; `max_pages` elevado; `refresh_finep_corpus --all` |
| **Evidência** | Reload 30/09/2026 → **31** chamadas abertas com PDF, **31/31** embeddings, manifest FINEP-only |
| **Lição** | Parâmetros de amostragem devem ser explícitos na metodologia experimental |

#### E09 — Detalhe do edital incompleto (só HTML / PDF único)

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Falta anexos, temas, região, prazo |
| **Causa** | Coleta rasa |
| **Solução** | `nestedFields=documentos`; download de edital+anexos; metadados (`region`, `prazo_proposta`, `themes`, `situacao`) no JSON + manifest |
| **Lição** | Qualidade do retrieval depende da qualidade da ingestão |

#### E10 — FAPESP / multi-fonte vs foco FINEP

| Campo | Detalhe |
|-------|---------|
| **Decisão** | Adiar FAPESP; manter FINEP como corpus piloto do TCC |
| **Motivo** | Regulamentos e público-alvo distintos; risco de diluir Hit@k e narrativa |
| **Solução** | Seed `--agency FINEP --purge-other` |
| **Lição** | Delimitação de escopo é decisão científica, não só de produto |

---

### 2.3 Interface Fase A e dados de negócio

#### E11 — Exclusão de material não atualizava contagem de projetos

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Dashboard `projects_count` inconsistente após delete |
| **Causa** | Removia `Document` sem cascata no `Project` associado / órfãos |
| **Solução** | Delete do PDF de projeto remove também o projeto; limpeza de órfãos no dashboard |
| **Lição** | Integridade referencial e métricas de UI precisam de testes de consistência |

#### E12 — Campo TRL no formulário gerava ruído

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Usuário/orientação pediu remoção de TRL/“TRF” dos forms |
| **Causa** | TRL institucional ≠ TRL do projeto; metadado frequentemente vazio no edital |
| **Solução** | Remoção do campo na UI; scoring passa a usar TRL de `form_data` ou `company.trl` quando existir; neutro se ausente |
| **Lição** | Modelo de dados do domínio deve espelhar o que o usuário realmente informa |

#### E13 — Preenchimento automático a partir do PDF falhava / frágil

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Form vazio ou parcial após upload |
| **Causa** | Extração heurística (regex) e PDFs heterogêneos |
| **Solução** | `app/pdf_form.py` com *guess* de título, áreas, orçamento; usuário edita antes de avaliar |
| **Teste** | `tests/test_pdf_form.py` |
| **Lição** | Humano-no-loop é parte do método, não falha do MVP |

#### E14 — Lookup de CNPJ (BrasilAPI)

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Autofill de porte/UF falha sob SSL corporativo |
| **Solução** | Cliente com fallback de verificação SSL; mapeamento de porte |
| **Arquivo** | `app/cnpj_lookup.py` |

#### E15 — Botão “reload” na UI não atualiza editais FINEP

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Expectativa de refresh do corpus pela tela |
| **Causa** | Coleta/indexação é pipeline CLI (`refresh_finep_corpus`), não endpoint da Fase A |
| **Solução** | Documentar; agendar via Task Scheduler (quinzenal) no Windows |
| **Lição** | Separar *produto* (UI) de *operações* (ETL) no texto do TCC |

---

### 2.4 Retrieval, scoring e ranking

#### E16 — Ranking dominado por similaridade textual (50%)

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Editais semanticamente próximos mas inelegíveis no topo |
| **Causa** | Matriz MVP: `0.50 sim + 0.20 área + 0.15 TRL + 0.15 porte` |
| **Solução** | **Matriz v2** (consultoria): estruturado 70% + semântico 30% |

```text
score = 0.30·sim + 0.25·área + 0.15·TRL + 0.15·porte
      + 0.10·região + 0.05·orçamento
```

Gates soft: prazo encerrado (×0,35), portes/região incompatíveis (teto), ordenação elegíveis primeiro.  
Docs: `docs/scoring.md` · testes: `tests/test_scoring.py`

#### E17 — Evaluate forçava `trl=None`

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Critério TRL sempre ~40 (“não informado”) na UI |
| **Causa** | Bug na montagem do `CompanyProfile` em `evaluate_project` |
| **Solução** | Usar TRL do formulário/empresa; UF e `budget_brl` no `ProjectQuery` |
| **Lição** | Integração API↔agentes precisa de teste de contrato, não só unitário das funções de nota |

#### E18 — Top 3 na UI vs expectativa de top 5

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Product spec e tela mostravam top 3 |
| **Solução** | `top_n=5`, `k=8` no evaluate; texto da página alinhado |
| **Lição** | Parâmetros de avaliação devem constar na seção experimental |

#### E19 — Metadados FINEP incompletos → notas “neutras”

| Campo | Detalhe |
|-------|---------|
| **Sintoma** | Pouca discriminação em TRL/porte/orçamento |
| **Causa** | `min_trl`, `company_sizes`, faixas de valor ainda pouco preenchidos no seed |
| **Solução atual** | Neutro ~70 para não punir artificialmente; região/prazo já vêm da API |
| **Trabalho futuro** | Extração estruturada de anexos (TRL, teto orçamentário, portes) |
| **Lição** | Declarar no TCC: *performance do ranking é upper-bounded pela qualidade do cadastro* |

#### E20 — Embeddings hashing vs MiniLM

| Campo | Detalhe |
|-------|---------|
| **Trade-off** | Hashing é offline e estável; qualidade semântica inferior a Sentence-Transformers |
| **Uso no TCC** | Demo Bayer/corporativo = hashing; experimento “ideal” = MiniLM em rede liberada |
| **Lição** | Reportar backend de embedding em toda tabela de Hit@k |

---

## 3. Suíte de testes automatizados

Execução típica:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

| Arquivo | O que valida | Relação com erros |
|---------|--------------|-------------------|
| `tests/test_config.py` | Carregamento de settings / `.env` | E03, E04 |
| `tests/test_embeddings.py` | Backend hashing / dimensão | E03, E20 |
| `tests/test_db_helpers.py` | Helpers de sessão/banco | E02 |
| `tests/test_extract_pdfs.py` | Extração de texto de PDF | E13 |
| `tests/test_pdf_form.py` | Guess de campos do formulário | E13 |
| `tests/test_finep_source.py` | Filtro situação / parsing FINEP | E07–E09 |
| `tests/test_retrieval.py` | Busca híbrida / reasons | E16, E20 |
| `tests/test_scoring.py` | Matriz v2, região, orçamento, ordenação | E16–E19 |
| `tests/test_llm.py` | Provider `none` / fallback | E03 |
| `tests/test_generation_pipeline.py` | Rascunho + seções de score | pipeline T-041 |

**Estado conhecido (30/09/2026):** `tests/test_scoring.py` + `tests/test_generation_pipeline.py` → **11 passed** após matriz v2.

### 3.1 Testes manuais / operacionais (checklist TCC)

| ID | Procedimento | Critério de sucesso |
|----|--------------|---------------------|
| M01 | `python -m scripts.check_env` | Conexão Neon OK |
| M02 | `python -m scripts.migrate_db` | Schema Fase A OK |
| M03 | `python -m scripts.refresh_finep_corpus --all` | N editais abertos indexados (ex.: 31) |
| M04 | Subir `uvicorn` + abrir `/` | Dashboard carrega |
| M05 | Cadastrar empresa (CNPJ) → projeto PDF → avaliar | Top 5 com breakdown e summary ALTA/MÉDIA/BAIXA |
| M06 | Excluir material de projeto | Contagens do dashboard coerentes |
| M07 | Smoke retrieval CLI / score CLI | Ranking estável e explicável |

---

## 4. Evidências experimentais já obtidas

### 4.1 Corpus FINEP (reload sem limite)

| Métrica | Valor |
|---------|-------|
| Filtro | Situação **Aberta** (`abert*`) |
| Chamadas com PDF | **31** |
| PDFs (novos + cache) | ~361 |
| Seed | FINEP-only, 31 upserts |
| Embeddings | 31/31 (backend hashing) |

### 4.2 Evolução da matriz de scoring

| Versão | Similaridade | Estruturado | Observação |
|--------|--------------|-------------|------------|
| MVP | 50% | 50% (área+TRL+porte) | Bom para demo rápida; frágil em elegibilidade |
| v2 | 30% | 70% (+ região + orçamento + gates) | Alinhada a prática de consultoria |

Faixas de interpretação: **≥75 ALTA**, **50–74 MÉDIA**, **&lt;50 BAIXA**.

### 4.3 Métricas ainda recomendadas para o capítulo de avaliação

Para enriquecer o TC1/defesa (além de “sistema funciona”):

1. **Hit@3 / Hit@5** com *ground truth* anotado (3–5 projetos exemplo + editais esperados)  
2. Comparar ranking MVP vs v2 no mesmo conjunto  
3. Comparar `hashing` vs `minilm` (quando rede permitir)  
4. Taxa de inelegíveis no top-5 antes/depois dos gates  
5. Tempo de pipeline (coleta → index → evaluate)

---

## 5. Limitações abertas (trabalhos futuros)

1. Extração automática de **TRL mínimo**, **portes** e **faixa orçamentária** a partir dos PDFs/anexos FINEP  
2. Gates rígidos no SQL do Retrieval (`enforce_trl`, `enforce_size`, região) ligados por padrão na UI  
3. Critérios de **instrumento** (subvenção vs crédito vs FIP) e **exige ICT/parceiro**  
4. Endpoint autenticado de *refresh* do corpus (hoje só CLI/Task Scheduler)  
5. Avaliação humana (especialista em fomento) para calibrar pesos  
6. Multi-fonte (FAPESP/CNPq) com taxonomia unificada  
7. Fase B (chat) fora do escopo congelado da Fase A

---

## 6. Mapa rápido: problema → arquivo

| Tema | Arquivos principais |
|------|---------------------|
| Coleta FINEP | `agents/sources/finep.py`, `agents/scraper_agent.py`, `scripts/refresh_finep_corpus.py` |
| Indexação | `scripts/seed_corpus.py`, `scripts/index_edicts.py`, `agents/indexer_agent.py` |
| Retrieval | `agents/retrieval_agent.py` |
| Scoring v2 | `agents/scoring_agent.py`, `docs/scoring.md` |
| Evaluate UI | `app/routes_fase_a.py`, `web/project-evaluate.html` |
| CNPJ / PDF form | `app/cnpj_lookup.py`, `app/pdf_form.py` |
| Embeddings offline | `app/embeddings.py`, `.env` (`EMBEDDING_BACKEND`) |
| Testes | `tests/*.py` |

---

## 7. Texto-modelo (pode colar na monografia)

> Durante o desenvolvimento do protótipo, adotou-se um ciclo iterativo de engenharia: cada falha observada em ambiente real (rede corporativa, inconsistência de dados, ranking enviesado por similaridade textual ou parâmetros de amostragem do coletor) foi diagnosticada, corrigida e, sempre que possível, coberta por teste automatizado ou checklist operacional. Destacam-se a migração para PostgreSQL/`pgvector` em nuvem (Neon) para independência de Docker local; o backend de embeddings *hashing* como fallback offline; a delimitação do corpus às chamadas FINEP com situação aberta; e a reformulação da matriz de pontuação, reduzindo o peso da similaridade semântica de 50% para 30% e ampliando critérios estruturados (tema, TRL, porte, região e orçamento), com penalidades por inelegibilidade. Esses ajustes aproximam o comportamento do sistema ao raciocínio de uma consultoria de fomento e tornam os resultados experimentais mais auditáveis.

---

## 8. Histórico de revisões deste diário

| Data | Mudança |
|------|---------|
| 30/09/2026 | Criação: consolidação E01–E20, suíte de testes, reload FINEP (31), matriz v2 |

*Documento vivo: novas falhas de demo/defesa devem ser acrescentadas no mesmo formato (contexto → sintoma → causa → solução → teste → lição).*
