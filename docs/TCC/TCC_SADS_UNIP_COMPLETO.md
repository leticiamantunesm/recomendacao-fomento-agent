# PARTE I — TCC COMPLETO

---

UNIVERSIDADE PAULISTA — UNIP  
[PREENCHER: CAMPUS]  
Curso de Ciência da Computação

---

**[PREENCHER: NOME COMPLETO DA AUTORA]**  
RA: [PREENCHER: RA]

---

# SADS — SISTEMA DE AGENTES DE IA PARA GESTÃO E SUBVENÇÃO DE EDITAIS:  
## um protótipo de apoio à decisão para recomendação de instrumentos de fomento à inovação

---

Trabalho de Conclusão de Curso apresentado ao Curso de Ciência da Computação da Universidade Paulista — UNIP, como requisito parcial para obtenção do título de Bacharela em Ciência da Computação.

Orientador(a): [PREENCHER: NOME DO ORIENTADOR]

[PREENCHER: CIDADE]  
2026

---

## FOLHA DE APROVAÇÃO

**Título:** SADS — Sistema de Agentes de IA para Gestão e Subvenção de Editais: um protótipo de apoio à decisão para recomendação de instrumentos de fomento à inovação

**Autora:** [PREENCHER: NOME COMPLETO DA AUTORA]

Trabalho de Conclusão de Curso aprovado como requisito parcial para obtenção do título de Bacharela em Ciência da Computação pela Universidade Paulista — UNIP.

Banca examinadora:

_________________________________  
Prof(a). [PREENCHER: ORIENTADOR(A)] — Orientador(a)

_________________________________  
Prof(a). [PREENCHER: MEMBRO 1]

_________________________________  
Prof(a). [PREENCHER: MEMBRO 2]

[PREENCHER: CIDADE], ____ de ______________ de 2026.

---

## RESUMO

Empresas e organizações que desenvolvem projetos de inovação enfrentam dificuldade para localizar, interpretar e comparar editais de fomento público, cujos critérios de elegibilidade, prazos e instrumentos (subvenção, crédito, parceria) variam entre instituições como FINEP, FAPs e BNDES. Este trabalho apresenta o SADS (Sistema de Agentes de IA para Gestão e Subvenção de Editais), um protótipo de sistema de apoio à decisão que cadastra organização e usuários, recebe o dossiê do projeto (PDF e formulário), cruza o perfil com um corpus indexado de editais e produz um ranking explicável de aderência. A solução foi implementada como monólito modular em Python com FastAPI, PostgreSQL/pgvector (Neon), embeddings via sentence-transformers (com fallback hashing), agentes próprios de coleta, indexação, recuperação, scoring e geração textual por template, além de interface web HTML/JS e landing Next.js. A metodologia caracteriza-se como pesquisa aplicada de desenvolvimento de artefato computacional, com requisitos reconstruídos a partir do código, decisões arquiteturais documentadas (ADRs) e validação por testes automatizados e manuais. Nos cenários avaliados, a bateria de recomendações com gabarito atingiu 10/10 casos de exemplo e o corpus de regressão v2 registrou 24 testes aprovados; a suíte pytest do repositório, na execução desta elaboração, apresentou 146 testes aprovados e 1 falha pontual em heurística de formulário. Limitações incluem corpus operacional piloto centrado na FINEP, autorização não obtida para APIs oficiais do BNDES (mantido apenas como opção ampla de crédito), geração textual sem LLM por padrão e autorização server-side incompleta em parte das rotas da Fase A. Conclui-se que o protótipo atende ao objetivo de apoiar a triagem inicial de instrumentos de fomento de forma explicável, sem substituir consultoria especializada nem garantir aprovação junto aos órgãos.

**Palavras-chave:** sistema de apoio à decisão; fomento à inovação; recuperação de informação; embeddings; FastAPI; editais; scoring.

---

## ABSTRACT

Companies and organizations that develop innovation projects often struggle to locate, interpret, and compare public funding calls, whose eligibility criteria, deadlines, and instruments (grants, credit, partnerships) differ across agencies such as FINEP, state research foundations, and BNDES. This work presents SADS (AI Agent System for Grant and Subsidy Management), a decision-support prototype that registers organizations and users, receives a project dossier (PDF and form), matches the profile against an indexed corpus of calls, and produces an explainable adherence ranking. The solution was implemented as a modular Python monolith with FastAPI, PostgreSQL/pgvector (Neon), sentence-transformers embeddings (with hashing fallback), custom agents for collection, indexing, retrieval, scoring, and template-based text generation, plus an HTML/JS web UI and a Next.js landing page. The methodology is applied research centered on building a software artifact, with requirements reconstructed from the codebase, documented architectural decisions (ADRs), and validation through automated and manual tests. In the evaluated scenarios, the recommendation battery with a gold set reached 10/10 example cases, and the v2 regression corpus recorded 24 passing tests; the repository pytest suite, when executed for this document, yielded 146 passed tests and one localized failure in form heuristics. Limitations include an operational pilot corpus focused on FINEP, lack of authorization for official BNDES APIs (BNDES kept only as a broad credit option), template-based generation with LLM disabled by default, and incomplete server-side authorization on part of Phase A routes. The prototype supports initial triage of funding instruments in an explainable way, without replacing specialized consulting or guaranteeing agency approval.

**Keywords:** decision support system; innovation funding; information retrieval; embeddings; FastAPI; public calls; scoring.

---

## LISTA DE FIGURAS

Figura 1 — Contexto do SADS (clientes, aplicação, dados e externos)  
Figura 2 — Fluxo de recomendação (projeto → retrieval → scoring → applications → UI)  
Figura 3 — Pipeline de agentes (coleta, indexação, recuperação, avaliação, geração)  
Figura 4 — Modelo lógico de dados (entidades principais)  
Figura 5 — Fluxo de autenticação (registro, login, token Bearer)  
Figura 6 — Tela de landing pública  
Figura 7 — Tela de dashboard  
Figura 8 — Tela de novo projeto / upload  
Figura 9 — Tela de relatório de avaliação  
Figura 10 — Diagrama de componentes software

---

## LISTA DE TABELAS

Tabela 1 — Requisitos funcionais reconstruídos (síntese)  
Tabela 2 — Matriz de pesos do scoring (v2)  
Tabela 3 — Principiais endpoints da API  
Tabela 4 — Suíte de testes automatizados por arquivo  
Tabela 5 — Resultados do gabarito de recomendações (síntese)  
Tabela 6 — Rastreabilidade objetivo × evidência (síntese)

---

## LISTA DE ABREVIATURAS E SIGLAS

| Sigla | Significado |
|-------|-------------|
| ADR | Architecture Decision Record |
| API | Application Programming Interface |
| BNDES | Banco Nacional de Desenvolvimento Econômico e Social |
| CNPJ | Cadastro Nacional da Pessoa Jurídica |
| FAPESP | Fundação de Amparo à Pesquisa do Estado de São Paulo |
| FINEP | Financiadora de Estudos e Projetos |
| HMAC | Hash-based Message Authentication Code |
| HTML | HyperText Markup Language |
| HTTP | HyperText Transfer Protocol |
| LLM | Large Language Model |
| ORM | Object-Relational Mapping |
| PBKDF2 | Password-Based Key Derivation Function 2 |
| PDF | Portable Document Format |
| REST | Representational State Transfer |
| SAD | Sistema de Apoio à Decisão |
| SADS | Sistema de Agentes de IA para Gestão e Subvenção de Editais |
| SQL | Structured Query Language |
| TCC | Trabalho de Conclusão de Curso |
| TRL | Technology Readiness Level |
| UI | User Interface |

---

## SUMÁRIO

1 INTRODUÇÃO  
  1.1 Contextualização  
  1.2 Problema de pesquisa  
  1.3 Objetivo geral  
  1.4 Objetivos específicos  
  1.5 Justificativa  
  1.6 Organização do trabalho  
2 FUNDAMENTAÇÃO TEÓRICA  
  2.1 Fomento à inovação e instrumentos públicos no Brasil  
  2.2 Sistemas de apoio à decisão  
  2.3 Recuperação de informação e busca semântica  
  2.4 Embeddings e similaridade  
  2.5 Geração aumentada por recuperação (RAG) e uso criterioso de LLM  
  2.6 Engenharia de software, APIs REST e aplicações web  
  2.7 Segurança em aplicações web  
  2.8 Testes de software  
  2.9 Trabalhos e soluções relacionadas  
3 METODOLOGIA  
  3.1 Classificação da pesquisa  
  3.2 Etapas do desenvolvimento  
  3.3 Levantamento e definição de requisitos  
  3.4 Tecnologias e critérios de escolha  
  3.5 Estratégia de desenvolvimento  
  3.6 Estratégia de testes e validação  
4 DESENVOLVIMENTO DA SOLUÇÃO  
  4.1 Visão geral  
  4.2 Requisitos  
  4.3 Arquitetura  
  4.4 Modelagem de dados  
  4.5 Backend e agentes  
  4.6 Frontend  
  4.7 APIs e integrações  
  4.8 Segurança  
  4.9 Principais funcionalidades  
5 TESTES, RESULTADOS E DISCUSSÃO  
  5.1 Planejamento dos testes  
  5.2 Testes realizados  
  5.3 Resultados  
  5.4 Discussão  
  5.5 Limitações  
6 CONSIDERAÇÕES FINAIS  
  6.1 Síntese dos resultados  
  6.2 Atendimento dos objetivos  
  6.3 Limitações  
  6.4 Trabalhos futuros  
REFERÊNCIAS  
APÊNDICES  
ANEXOS  

---

# 1 INTRODUÇÃO

## 1.1 Contextualização

A inovação tecnológica é reconhecida como fator de competitividade empresarial e de política pública. No Brasil, a Lei nº 10.973, de 2 de dezembro de 2004 — conhecida como Lei de Inovação — estabelece incentivos à pesquisa científica e tecnológica no ambiente produtivo e prevê instrumentos como subvenção econômica, financiamento e participação societária (BRASIL, 2004). Agências e instituições como a Financiadora de Estudos e Projetos (FINEP) operam chamadas e fluxos contínuos de apoio não reembolsável e reembolsável, com exigências de contrapartida, elegibilidade e alinhamento a prioridades estratégicas (FINEP, 2024).

Na prática, o acesso a esses recursos depende da capacidade da organização de acompanhar portais distintos, interpretar regulamentos extensos e decidir rapidamente se um instrumento é compatível com o porte da empresa, a maturidade tecnológica do projeto (TRL), a natureza do gasto (pesquisa versus modernização/Capex) e os prazos. Esse processo costuma ser manual, disperso e sujeito a erros de enquadramento — por exemplo, pleitear subvenção de P&D para um projeto de mera reposição de equipamentos.

Soluções comerciais de “radar de editais” e matchmaking entre projetos e fomento têm proliferado no mercado brasileiro, reforçando que o problema de priorização de janelas de captação é reconhecido por gestores de P&D. Contudo, para fins acadêmicos e de protótipo, permanece a necessidade de um artefato transparente, auditável e explicável, no qual as regras de elegibilidade e o ranking possam ser inspecionados e testados.

## 1.2 Problema de pesquisa

Diante da dispersão de editais e da heterogeneidade de critérios, formula-se o seguinte problema:

**Como apoiar, de maneira estruturada e explicável, a identificação de mecanismos de fomento compatíveis com o perfil de uma organização e de seu projeto de inovação, por meio de um sistema computacional?**

O problema afeta, em especial, micro, pequenas e médias empresas inovadoras, startups e equipes de P&D com capacidade limitada de consultoria especializada. Uma solução computacional faz sentido porque parte da triagem envolve cruzamento repetitivo de atributos estruturados (porte, UF, TRL, áreas) e similaridade textual entre o dossiê do projeto e o texto dos editais — tarefas adequadas a recuperação de informação, embeddings e regras de negócio implementáveis.

## 1.3 Objetivo geral

Desenvolver e validar um protótipo de sistema de apoio à decisão — o SADS — capaz de cadastrar organização e usuários, receber o projeto (PDF e formulário), recuperar editais candidatos em um corpus indexado e produzir um ranking explicável de aderência, com registro histórico das recomendações.

## 1.4 Objetivos específicos

1. Modelar e persistir dados de organização, usuários, projetos, documentos, editais e aplicações recomendadas.  
2. Implementar autenticação com armazenamento seguro de senhas e sessão por token.  
3. Coletar e indexar um corpus piloto de editais (FINEP), com suporte experimental a outras fontes.  
4. Implementar recuperação híbrida (filtros estruturados + similaridade vetorial) e scoring multicritério explicável.  
5. Disponibilizar interface web para o fluxo principal da Fase A (cadastro, projeto, avaliação, aplicações).  
6. Validar o comportamento por testes automatizados e cenários documentados (incluindo regressões e casos “armadilha”).  
7. Documentar decisões arquiteturais, limitações e tentativas de integração externa (inclui BNDES).

## 1.5 Justificativa

Do ponto de vista social e econômico, melhorar a triagem inicial de fomento pode reduzir esforço desperdiçado em propostas incompatíveis e acelerar o encaminhamento a instrumentos adequados (subvenção versus crédito). Do ponto de vista acadêmico, o tema integra Engenharia de Software, recuperação de informação, aprendizado de representação textual e sistemas de apoio à decisão — áreas centrais da Ciência da Computação. Do ponto de vista técnico, o repositório já materializa um PoC operacional (API 0.4.0, UI Fase A, pipeline de agentes), o que permite confrontar objetivos com evidências de implementação e teste, em conformidade com a expectativa de um TCC defensável.

## 1.6 Organização do trabalho

O Capítulo 2 apresenta a fundamentação teórica do domínio e dos fundamentos computacionais. O Capítulo 3 descreve a metodologia. O Capítulo 4 detalha o desenvolvimento da solução. O Capítulo 5 discute testes, resultados e limitações. O Capítulo 6 traz as considerações finais.

---

# 2 FUNDAMENTAÇÃO TEÓRICA

## 2.1 Fomento à inovação e instrumentos públicos no Brasil

A política brasileira de estímulo à inovação combina marco legal e operação por agências. A Lei nº 10.973/2004 dispõe sobre incentivos à inovação e à pesquisa no ambiente produtivo e, em sua redação atualizada, elenca instrumentos como subvenção econômica, financiamento, participação societária, bônus tecnológico e incentivos fiscais, entre outros (BRASIL, 2004). A FINEP, como secretaria-executiva do FNDCT em diversos contextos institucionais, opera modalidades de financiamento não reembolsável e reembolsável, inclusive subvenção econômica com compartilhamento de risco e exigência de contrapartida (FINEP, 2024).

Essa diversidade de instrumentos implica que **ader natureza do projeto importa**: atividades de pesquisa, desenvolvimento e inovação com risco tecnológico tendem a se alinhar a subvenção ou chamadas de P&D; modernização operacional e aquisição de bens de capital costumam se aproximar de crédito ou consultoria. Sistemas que ignoram essa distinção tendem a recomendar subvenção indevidamente — falha observada e corrigida em regressões do próprio SADS (Capítulo 5).

O nível de maturidade tecnológica (TRL — *Technology Readiness Level*), conceito popularizado em contextos de engenharia e agências tecnológicas, é frequentemente usado em editais para delimitar o estágio elegível do projeto. No SADS, o TRL da empresa/projeto entra como critério ponderado no scoring quando o edital informa mínimo exigido.

## 2.2 Sistemas de apoio à decisão

Sistemas de Apoio à Decisão (SAD) auxiliam gestores a estruturar problemas semiestruturados, combinando dados, modelos e interface interativa (TURBAN; ARONSON; LIANG, 2005; POWER, 2002). O SADS enquadra-se como SAD de triagem: não decide a aprovação do órgão financiador, mas ordena opções e expõe justificativas (forças, fraquezas, breakdown), permitindo que a analista humana confirme ou descarte encaminhamentos.

Características alinhadas à literatura de SAD presentes no protótipo incluem: (i) base de dados de editais e projetos; (ii) modelo de recomendação (retrieval + scoring); (iii) interface para inspeção do resultado; (iv) persistência do histórico de aplicações para acompanhamento.

## 2.3 Recuperação de informação e busca semântica

A Recuperação de Informação (*Information Retrieval* — IR) trata de satisfazer uma necessidade informacional a partir de uma coleção de documentos, tipicamente retornando uma lista ordenada por relevância (MANNING; RAGHAVAN; SCHÜTZE, 2008). No modelo clássico de espaço vetorial, documentos e consultas são representados como vetores e comparados por similaridade — frequentemente o cosseno (SALTON; WONG; YANG, 1975; MANNING; RAGHAVAN; SCHÜTZE, 2008).

No SADS, a “consulta” é o texto/perfil do projeto e a “coleção” é o corpus de editais. Além da dimensão semântica, aplicam-se filtros estruturados (agência, áreas, porte), o que caracteriza uma recuperação **híbrida**: metadados + similaridade vetorial. Essa combinação é coerente com a necessidade de elegibilidade formal (porte, região) não reduzível a similaridade textual.

## 2.4 Embeddings e similaridade

Representações densas de texto (*embeddings*) permitem comparar significados além da sobreposição lexical. Reimers e Gurevych (2019) propuseram o Sentence-BERT (SBERT), adaptação de redes BERT com arquitetura siamesa/triplet para produzir embeddings de sentenças comparáveis por cosseno de forma eficiente. Bibliotecas como *sentence-transformers* popularizaram modelos prontos; o SADS utiliza, por padrão, `sentence-transformers/all-MiniLM-L6-v2` (384 dimensões), armazenando vetores no PostgreSQL via extensão **pgvector**.

Quando o download do modelo é inviável (rede, ambiente), o sistema oferece backend `hashing` (ADR-008), preservando dimensionalidade compatível com o schema, ainda que com qualidade semântica inferior. Essa dualidade evidencia trade-off entre fidelidade semântica e operacionalidade do PoC.

## 2.5 Geração aumentada por recuperação (RAG) e uso criterioso de LLM

Lewis et al. (2020) formalizaram a *Retrieval-Augmented Generation* (RAG), combinando memória paramétrica (modelo generativo) e não paramétrica (índice recuperável) para tarefas intensivas em conhecimento. O padrão “recuperar e depois gerar” reduz, em muitos cenários, respostas desconectadas da base factual, desde que a recuperação seja adequada.

O SADS **aproxima-se** desse padrão no fluxo retrieve → score → generate, porém, por decisão explícita (ADR-003), o provedor de LLM padrão é `none`: a geração textual usa **templates** determinísticos. Assim, o sistema prioriza explicabilidade e custo zero no MVP, deixando chat com LLM como Fase B. A fundamentação de Lewis et al. (2020) justifica a arquitetura de recuperação + geração, enquanto a escolha de desligar o LLM no PoC é uma restrição de produto e privacidade, não uma negação do paradigma.

## 2.6 Engenharia de software, APIs REST e aplicações web

A Engenharia de Software orienta o desenvolvimento sistemático de artefatos com requisitos, arquitetura, implementação e verificação (SOMMERVILLE, 2011; PRESSMAN; MAXIM, 2016). O SADS organiza-se em módulos (`app/`, `agents/`, `db/`, `web/`, `scripts/`), com contratos Pydantic e documentação OpenAPI gerada pelo FastAPI.

O estilo arquitetural de APIs REST, descrito por Fielding (2000), influencia a exposição de recursos via HTTP (empresas, projetos, aplicações) com métodos GET/POST/PATCH/DELETE. O frontend autenticado é HTML/CSS/JS estático consumindo a API; a landing institucional usa Next.js com export estático — decisão de velocidade de entrega da Fase A (ADR-005), em detrimento de uma SPA única.

## 2.7 Segurança em aplicações web

A OWASP destaca riscos recorrentes em aplicações web, incluindo falhas de autenticação e controle de acesso (OWASP, 2021). Boas práticas de armazenamento de senha recomendam funções de derivação com custo computacional, como PBKDF2 (NIST, 2010). O SADS armazena senhas com PBKDF2-SHA256 (200 mil iterações) e compara hashes com `hmac.compare_digest`; sessões usam token assinado HMAC com TTL configurável.

Contudo, segurança não se resume a hash de senha. A literatura e a prática de mercado enfatizam autorização consistente no servidor. No SADS, a crítica documentada é que várias rotas da Fase A ainda dependem do `company_id` enviado pelo cliente, sem `Depends(get_current_user)` generalizado — limitação explícita no Capítulo 5.

## 2.8 Testes de software

Testes automatizados aumentam a confiança em regressões e documentam o comportamento esperado (SOMMERVILLE, 2011). O SADS utiliza **pytest** para testes unitários e de pipeline com fixtures (HTML de portais, gabaritos de recomendação, mocks HTTP). Testes manuais de smoke (ambiente, migrate, refresh FINEP, evaluate) estão descritos em diário técnico do repositório. Esta combinação alinha-se a uma estratégia pragmática de PoC: forte cobertura das regras de scoring/retrieval e validação manual do fluxo ponta a ponta.

## 2.9 Trabalhos e soluções relacionadas

No mercado brasileiro existem plataformas de radar/matchmaking de editais e agentes comerciais de apoio à captação (monitoramento contínuo, ranking de aderência, apoio à estruturação de propostas). Em comum com o SADS está a ideia de cruzar perfil organizacional e oportunidade de fomento. Diferenciam-se, no escopo deste TCC, o caráter de **protótipo acadêmico aberto à inspeção**, o ranking com pesos e gates explícitos, a geração por template (sem prometer “aprovação por IA”) e a honestidade quanto ao corpus piloto FINEP e à falha de autorização em APIs do BNDES.

Não se afirma superioridade empírica frente a produtos comerciais: não houve estudo comparativo controlado com usuários externos. A contribuição é o artefato + a evidência de testes + a documentação de decisões e limites.

---

# 3 METODOLOGIA

## 3.1 Classificação da pesquisa

Sob a ótica de Gil (2008) e Prodanov e Freitas (2013), o trabalho classifica-se como:

- **Natureza:** pesquisa aplicada (produção de artefato útil a um problema concreto).  
- **Objetivos:** exploratória e descritiva quanto ao domínio; tecnológica quanto ao produto.  
- **Abordagem:** predominantemente qualitativa na análise de requisitos e decisões; quantitativa pontual nos resultados de suítes de teste (contagens de aprovação/reprovação), sem experimento estatístico formal com amostragem de usuários.  
- **Procedimentos:** desenvolvimento de sistema / construção de artefato computacional, com elementos de estudo de caso técnico sobre o próprio repositório.

## 3.2 Etapas do desenvolvimento

As etapas efetivamente refletidas no repositório e na documentação interna foram:

1. **Levantamento inicial do problema** — dificuldade de triagem de editais (manual do produto / resumo do grupo).  
2. **Definição do escopo Fase A** — cadastro, PDF, ranking, histórico; chat LLM e SSO na Fase B.  
3. **Reconstrução/definição de requisitos** — RF/RNF a partir do código e docs (não houve elicitation formal com stakeholders externos documentada).  
4. **Decisões de arquitetura** — ADRs 001–009.  
5. **Modelagem de dados** — SQL em `db/init` + ORM.  
6. **Implementação do backend e agentes**.  
7. **Implementação da UI e landing**.  
8. **Integrações** — FINEP, BrasilAPI; tentativa BNDES.  
9. **Testes automatizados e manuais**.  
10. **Análise de falhas e correções** (ex.: Aurora / modernização × crédito).  
11. **Documentação técnica e deste TCC**.

## 3.3 Levantamento e definição de requisitos

Os requisitos funcionais e não funcionais foram **reconstruídos** a partir do comportamento implementado e da documentação do repositório (`DOCUMENTACAO_TECNICA_DESENVOLVIMENTO.md`). Isso é uma limitação metodológica: não se trata de um documento de requisitos prévio assinado por cliente. Em contrapartida, a rastreabilidade requisito → código → teste é forte.

## 3.4 Tecnologias e critérios de escolha

Critérios observados nas ADRs e no README:

| Tecnologia | Critério / justificativa técnica |
|------------|----------------------------------|
| Python + FastAPI | Produtividade, tipagem com Pydantic, OpenAPI automático |
| Neon PostgreSQL + pgvector | Vetores e dados relacionais no mesmo SGBD; setup rápido para TCC |
| sentence-transformers | Embeddings de sentenças prontos (linha SBERT) |
| Hashing fallback | Continuidade offline/CI |
| LLM `none` + template | Custo zero e menor exposição de dados no MVP |
| HTML estático + Next landing | Entrega rápida da Fase A |
| httpx + BeautifulSoup + pypdf | Coleta e extração sem OCR |
| pytest | Validação automatizada das regras |

## 3.5 Estratégia de desenvolvimento

O desenvolvimento seguiu backlog incremental (tarefas T-001…T-042 e UI-A) documentado no README/status, sem metodologia ágil formal (Scrum/Kanban) identificada nos materiais. A arquitetura de agentes em Python puro (ADR-002) priorizou controle de contratos e testabilidade em relação a frameworks de orquestração (LangChain/CrewAI), citados apenas como opcionais e **ausentes** do runtime.

## 3.6 Estratégia de testes e validação

- **Unitários:** scoring, retrieval, embeddings, PDF/heurísticas, fontes HTML com fixtures, client BNDES mockado.  
- **Pipeline/regressão:** gabarito de recomendações; corpus v2 GOOD/BAD; caso Aurora.  
- **Manuais:** smoke de ambiente, migrate, refresh FINEP, fluxo PDF→evaluate.  
- **Não realizados (declarado):** teste formal de usabilidade com usuários; load/performance; penetração de segurança; Hit@k multi-fonte em produção; E2E de autorização server-side completo.

---

# 4 DESENVOLVIMENTO DA SOLUÇÃO

## 4.1 Visão geral

O SADS é um monólito modular servido por Uvicorn: API FastAPI, arquivos estáticos `web/`, landing exportada e acesso ao Neon. Jobs CLI (`scripts/`) atualizam corpus e índice. O fluxo principal do usuário autenticado é: registrar/login → completar empresa → criar projeto (PDF) → avaliar → inspecionar ranking → acompanhar applications.

[INSERIR FIGURA 1 – Diagrama de contexto: Visitante→Landing; Usuário→UI web; API FastAPI; Neon; agents; FINEP; BrasilAPI]  
Fonte: Elaborado pela autora (2026), a partir de `docs/ARQUITETURA_SADS.md`.

## 4.2 Requisitos

**Tabela 1 — Síntese de requisitos funcionais (reconstruídos)**

| ID | Descrição | Status |
|----|-----------|--------|
| RF01–RF02 | Cadastro e autenticação | Implementado |
| RF03 | Recuperação de senha | Parcial (SMTP opcional) |
| RF04–RF06 | Dashboard, empresa, equipe | Implementado (RBAC fino parcial) |
| RF07–RF09 | PDF, extração, evaluate/ranking | Implementado (extração sem OCR) |
| RF10–RF12 | Applications, outcomes, documentos | Implementado |
| RF13 | CNPJ (BrasilAPI) | Implementado |
| RF14–RF16 | Corpus FINEP, embeddings, generation template | Implementado (piloto) |
| RF17 | Landing | Implementado |
| RF18–RF19 | Chat LLM, SSO | Planejado |
| RF20 | Multi-fonte | Parcial |

Regras de negócio relevantes: score 0–100; elegíveis primeiro; faixas ALTA/MÉDIA/BAIXA; metadados ausentes → nota neutra ~70 no critério; score **não** garante aprovação; projetos privados não viram item do corpus público de editais.

## 4.3 Arquitetura

[INSERIR FIGURA 2 – Fluxo: projects.raw_text + company → Retrieval → EdictMatch → Scoring → applications → project-evaluate]  
Fonte: Elaborado pela autora (2026).

[INSERIR FIGURA 3 – Agentes: Scraper → Indexer → Retrieval → Scoring → Generation; Gate0 project_risk; FormExtraction]  
Fonte: Elaborado pela autora (2026).

Componentes: `app/main.py` (gateway), `routes_auth.py`, `routes_fase_a.py`, `agents/*`, `db/models.py`, `web/*`, `landing/`.

## 4.4 Modelagem de dados

Entidades principais (`db/models.py` e SQL `db/init`):

- **Company** — perfil organizacional (porte, TRL, áreas, CNPJ, UF etc.).  
- **Employee** — usuário ligado à empresa (e-mail único por empresa, `password_hash`, `role`).  
- **Project** — título, PDF, `raw_text`, `form_data`, status.  
- **Document** — materiais anexos.  
- **Edict** — corpus de editais (`external_id`, agência, texto, URL, metadados); embedding em coluna `vector(384)` no SQL.  
- **Application** — recomendação persistida (score, breakdown JSONB, strengths/weaknesses, status/outcomes).

[INSERIR FIGURA 4 – Diagrama ER simplificado Company 1-N Employee/Project/Document/Application; Edict 1-N Application]  
Fonte: Elaborado pela autora (2026).

## 4.5 Backend e agentes

**Coletor (`scraper_agent` + `sources/`):** FINEP é a fonte piloto operacional. FAPESP, Embrapii, CNPq, Centelha possuem coletores em graus variados de maturidade. O BNDES, após ADR-009, expõe apenas entrada institucional ampla (`bndes-credito-institucional`), sem catálogo de linhas específicas.

**Indexador:** gera embeddings e persiste vetores.

**Retrieval:** busca híbrida SQL + similaridade.

**Gate 0 (`project_risk`):** distingue P&D/risco tecnológico de modernização/Capex; emite alertas e *redirects* (crédito BNDES amplo, Sebraetec, fomento estadual).

**Scoring:** matriz v2 (Tabela 2) + hard/soft gates (prazo, porte, TRL, região, rubricas vedadas em subvenção, preferência a crédito quando não há P&D).

**Tabela 2 — Matriz de pesos do scoring (v2)**

| Critério | Peso |
|----------|------|
| Similaridade semântica | 0,30 |
| Tema/áreas | 0,25 |
| TRL | 0,15 |
| Porte | 0,15 |
| Região | 0,10 |
| Orçamento | 0,05 |

**Generation:** template quando `LLM_PROVIDER=none`.

**Orquestrador:** encadeia retrieve → score → generate → artefato Markdown (pipeline CLI/`submit-project`).

## 4.6 Frontend

Páginas em `web/`: login, register, forgot/reset password, dashboard, project-new, project-evaluate, applications, materials, employee, company. Landing Next em `landing/` exportada para `landing/out/`.

[INSERIR FIGURA 6 – Screenshot `docs/fotos/01_landing.png`]  
Fonte: Captura do sistema (2026).

[INSERIR FIGURA 7 – Screenshot `docs/fotos/02_dashboard.png`]  
Fonte: Captura do sistema (2026).

[INSERIR FIGURA 8 – Screenshot `docs/fotos/03_project_new.png`]  
Fonte: Captura do sistema (2026).

[INSERIR FIGURA 9 – Screenshot `docs/fotos/07_project_evaluate.png`]  
Fonte: Captura do sistema (2026).

## 4.7 APIs e integrações

**Tabela 3 — Principais endpoints**

| Método | Caminho | Função |
|--------|---------|--------|
| GET | `/health` | Saúde da API |
| POST | `/api/v1/auth/register` | Cadastro |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Sessão atual |
| POST | `/api/v1/projects` | Criar projeto |
| POST | `/api/v1/projects/{id}/evaluate` | Avaliar / ranking |
| GET/PATCH | `/api/v1/applications` | Recomendações |
| GET | `/api/v1/cnpj/{cnpj}` | Autofill CNPJ |
| GET | `/api/v1/dashboard` | Métricas |

Integrações: API FINEP (corpus); BrasilAPI (CNPJ); tentativa Developers@BNDES (client em `app/integrations/bndes/`, **fora do motor** — autorização da Loja não obtida).

## 4.8 Segurança

Implementado: PBKDF2-SHA256; token HMAC; segredos em `.env`; LLM off por padrão; multi-tenant lógico por `company_id`.

Limitações: autorização incompleta em rotas Fase A; RBAC fino parcial; HTTPS/LGPD formal dependentes de implantação; ausência de auditoria de penetração.

[INSERIR FIGURA 5 – Fluxo register/login → token Bearer → chamadas API]  
Fonte: Elaborado pela autora (2026).

## 4.9 Principais funcionalidades

1. **Onboarding** — cria Company + Employee admin.  
2. **Gestão cadastral** — empresa, equipe, materiais.  
3. **Ingestão de projeto** — PDF → texto → sugestão de campos.  
4. **Avaliação** — Gate 0 + retrieval + scoring + relatório.  
5. **Histórico** — applications e outcomes.  
6. **Operação de corpus** — scripts CLI de refresh/index (não pela UI).

---

# 5 TESTES, RESULTADOS E DISCUSSÃO

## 5.1 Planejamento dos testes

O planejamento implícito no repositório privilegia: (i) correção das regras de elegibilidade/scoring; (ii) parsers de fontes; (iii) regressão de recomendações com gabarito; (iv) smoke manual do caminho feliz. Não há plano formal de testes de aceitação com usuários finais.

## 5.2 Testes realizados

**Tabela 4 — Arquivos de teste e objetivo**

| Arquivo | Objetivo |
|---------|----------|
| `test_scoring.py` | Pesos, ordenação, critérios |
| `test_retrieval.py` | Cosseno e razões |
| `test_project_risk.py` | Gate 0 modernização × P&D |
| `test_instruments.py` | Taxonomia de instrumentos |
| `test_finep_source.py` / `test_multi_sources.py` | Parsers de portais (fixtures) |
| `test_bndes_client.py` | Client OAuth mock (integração não usada no motor) |
| `test_pdf_form.py` / `test_form_extraction_agent.py` | Heurísticas de formulário |
| `test_embeddings.py` | Chunking / hashing 384-d |
| `test_llm.py` / `test_generation_pipeline.py` | Template e pipeline |
| `test_sads_recommendations.py` | Gabarito 10 exemplos |
| `test_sads_corpus_v2.py` | GOOD/BAD regressão |
| `test_aurora_frigorifico.py` | Modernização deve priorizar crédito |

Testes manuais (diário): check_env, migrate, refresh FINEP, uvicorn, PDF→evaluate.

## 5.3 Resultados

### 5.3.1 Evidência de execução automatizada (esta elaboração)

Na execução de `pytest tests` realizada para este documento: **146 passed, 1 failed** (`test_pdf_form.py::test_semente_viva_heuristic_smoke`). A falha pontual indica regressão/fragilidade em heurística de um PDF de exemplo, não invalida o conjunto de testes de scoring/recomendação, mas deve ser registrada honestamente.

### 5.3.2 Gabarito e regressões documentadas

Conforme `docs/TCC/sads_test_report.md` (registros de 10/11/2026 no repositório): bateria de recomendações e project_risk com dezenas de testes aprovados; corpus v2 com 24 testes; gabarito 01–10 com **10/10 PASS** no cenário documentado. O caso **BUG_01 Aurora** documenta falha observada na UI antes da correção (orçamento fantasma / ranking sem crédito) e a expectativa de PASS após correção de parser e preferência a crédito.

**Tabela 5 — Síntese de resultados de recomendação (documentados)**

| Conjunto | Resultado documentado |
|----------|----------------------|
| Gabarito exemplos 01–10 | 10/10 PASS (relatório TCC) |
| Corpus v2 GOOD/BAD | 24 passed (relatório) |
| Aurora (pós-correção, teste automatizado) | esperado PASS; bug de UI pré-correção documentado como FAIL |
| Suíte completa (execução desta redação) | 146 passed, 1 failed (heurística PDF) |

### 5.3.3 Resultados de implementação (não confundir com qualidade percebida)

O sistema **disponibiliza** autenticação, evaluate, ranking com breakdown, persistência de applications e operação FINEP. Isso é evidência de implementação, não de satisfação de usuários (não mensurada).

## 5.4 Discussão

Os testes mostram que o núcleo de decisão (Gate 0 + scoring + injeção de crédito em modernização) está sob controle de regressão. A literatura de IR e SAD apoia a separação entre recuperação candidata e ordenação multicritério explicável (MANNING; RAGHAVAN; SCHÜTZE, 2008; TURBAN; ARONSON; LIANG, 2005). A escolha de pesos fixos (ADR-004) favorece auditabilidade no TCC, em troca de não empregar ainda AHP/TOPSIS.

A tentativa de integração BNDES ilustra limitação externa: sem autorização na Loja de APIs, o contrato OAuth completo não foi operacionalizado; a decisão ADR-009 evita falso detalhamento de programas. Isso é resultado negativo útil academicamente.

A falha isolada em heurística PDF reforça que extração sem OCR e baseada em padrões textuais é frágil — alinhado à limitação já declarada (RF08 parcial).

## 5.5 Limitações

1. Corpus operacional piloto FINEP (ADR-006).  
2. BNDES apenas amplo (ADR-009).  
3. LLM desligado por padrão.  
4. Authz server-side incompleta.  
5. Sem estudo de usabilidade com amostra de usuários.  
6. Sem métricas formais de desempenho/carga.  
7. Multi-fonte e Hit@k pendentes.  
8. Extração PDF sem OCR; 1 teste de heurística falhou na suíte completa desta execução.

---

# 6 CONSIDERAÇÕES FINAIS

## 6.1 Síntese dos resultados

Foi desenvolvido o protótipo SADS, sistema de apoio à decisão para triagem de instrumentos de fomento, com pipeline de agentes, API FastAPI, banco vetorial e interface web. Testes automatizados e relatórios internos evidenciam comportamento correto nos gabaritos de recomendação documentados, com limitações explícitas de escopo e uma falha pontual de heurística na suíte completa executada nesta elaboração.

## 6.2 Atendimento dos objetivos

| Objetivo específico | Situação |
|---------------------|----------|
| Modelar/persistir dados | Atendido |
| Autenticação segura de senha/token | Atendido (authz ampla pendente) |
| Corpus FINEP + indexação | Atendido (piloto) |
| Retrieval + scoring explicável | Atendido |
| UI Fase A | Atendido |
| Validação por testes | Atendido parcialmente (cobertura forte de regras; usabilidade não avaliada) |
| Documentar decisões/limites/BNDES | Atendido (ADR-009) |

O objetivo geral foi alcançado no nível de **protótipo acadêmico defensável**, não de produto comercial consolidado.

## 6.3 Limitações

Reiteram-se as limitações do Capítulo 5: generalização além da FINEP, autorização BNDES, LLM, autorização de API, ausência de avaliação com usuários e fragilidade de heurísticas de PDF.

## 6.4 Trabalhos futuros

1. Enforcement de `Depends(get_current_user)` em todas as rotas sensíveis.  
2. Ampliação controlada do corpus e avaliação Hit@k.  
3. Retomar integração BNDES **se** houver autorização oficial.  
4. Calibração de pesos (AHP/TOPSIS) com especialistas.  
5. OCR e melhoria da extração.  
6. Chat LLM opcional com política de privacidade.  
7. Testes de usabilidade e segurança ofensiva controlada.

---

# REFERÊNCIAS

BRASIL. *Lei nº 10.973, de 2 de dezembro de 2004.* Dispõe sobre incentivos à inovação e à pesquisa científica e tecnológica no ambiente produtivo e dá outras providências. Brasília, DF: Presidência da República, 2004. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.973.htm. Acesso em: 10 nov. 2026.

FIELDING, R. T. *Architectural styles and the design of network-based software architectures.* 2000. Thesis (Doctor of Philosophy) — University of California, Irvine, 2000. Disponível em: https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm. Acesso em: 10 nov. 2026.

FINEP. *Financiamento não reembolsável.* Rio de Janeiro: Finep, [2024?]. Disponível em: https://www.finep.gov.br/financiamento-nao-reembolsavel. Acesso em: 10 nov. 2026.

GIL, A. C. *Como elaborar projetos de pesquisa.* 4. ed. São Paulo: Atlas, 2008.

LEWIS, P. et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NeurIPS), 33., 2020. *Proceedings* [...]. [S. l.]: NeurIPS, 2020. Disponível em: https://arxiv.org/abs/2005.11401. Acesso em: 10 nov. 2026.

MANNING, C. D.; RAGHAVAN, P.; SCHÜTZE, H. *Introduction to information retrieval.* Cambridge: Cambridge University Press, 2008.

NIST. *Recommendation for password-based key derivation:* Part 1: Storage applications. NIST Special Publication 800-132. Gaithersburg: National Institute of Standards and Technology, 2010. Disponível em: https://csrc.nist.gov/publications/detail/sp/800-132/final. Acesso em: 10 nov. 2026.

OWASP FOUNDATION. *OWASP Top Ten.* 2021. Disponível em: https://owasp.org/www-project-top-ten/. Acesso em: 10 nov. 2026.

POWER, D. J. *Decision support systems:* concepts and resources for managers. Westport: Quorum Books, 2002.

PRESSMAN, R. S.; MAXIM, B. R. *Engenharia de software:* uma abordagem profissional. 8. ed. Porto Alegre: AMGH, 2016.

PRODANOV, C. C.; FREITAS, E. C. *Metodologia do trabalho científico:* métodos e técnicas da pesquisa e do trabalho acadêmico. 2. ed. Novo Hamburgo: Feevale, 2013.

REIMERS, N.; GUREVYCH, I. Sentence-BERT: sentence embeddings using Siamese BERT-networks. In: CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING AND THE 9TH INTERNATIONAL JOINT CONFERENCE ON NATURAL LANGUAGE PROCESSING (EMNLP-IJCNLP), 2019, Hong Kong. *Proceedings* [...]. Stroudsburg: Association for Computational Linguistics, 2019. p. 3982-3992. DOI: https://doi.org/10.18653/v1/D19-1410.

SALTON, G.; WONG, A.; YANG, C. S. A vector space model for automatic indexing. *Communications of the ACM*, New York, v. 18, n. 11, p. 613-620, 1975.

SOMMERVILLE, I. *Engenharia de software.* 9. ed. São Paulo: Pearson Prentice Hall, 2011.

TURBAN, E.; ARONSON, J. E.; LIANG, T.-P. *Decision support systems and intelligent systems.* 7. ed. Upper Saddle River: Pearson Prentice Hall, 2005.

UNIVERSIDADE PAULISTA. *Guia de normalização para apresentação de trabalhos acadêmicos da Universidade Paulista:* ABNT. São Paulo: UNIP, 2025. [PENDENTE DE CONFIRMAÇÃO DA AUTORA: dados editoriais completos conforme exemplar impresso/PDF utilizado].

FASTAPI. *Documentation.* Disponível em: https://fastapi.tiangolo.com/. Acesso em: 10 nov. 2026. *(documentação oficial de tecnologia)*

POSTGRESQL. *PostgreSQL documentation.* Disponível em: https://www.postgresql.org/docs/. Acesso em: 10 nov. 2026. *(documentação oficial)*

PGVECTOR. *pgvector:* open-source vector similarity search for Postgres. Disponível em: https://github.com/pgvector/pgvector. Acesso em: 10 nov. 2026. *(documentação oficial)*

---

# APÊNDICES

## APÊNDICE A — Lista de arquivos-chave do repositório

`app/main.py`, `app/auth.py`, `app/routes_fase_a.py`, `app/routes_auth.py`, `agents/scoring_agent.py`, `agents/retrieval_agent.py`, `agents/project_risk.py`, `agents/sources/finep.py`, `agents/sources/bndes.py`, `db/models.py`, `db/init/*.sql`, `docs/DECISOES_ARQUITETURAIS.md`, `tests/test_sads_recommendations.py`, `docs/TCC/sads_test_report.md`.

## APÊNDICE B — ADRs (síntese)

ADR-001 Neon+pgvector; ADR-002 agentes Python puro; ADR-003 LLM none; ADR-004 pesos fixos; ADR-005 UI HTML+landing Next; ADR-006 corpus FINEP; ADR-007 multi-tenant company_id; ADR-008 hashing fallback; ADR-009 BNDES amplo / API não autorizada.

## APÊNDICE C — Sugestão de código mínimo (não exaustivo)

Trechos extensos devem ser consultados no repositório. Evitar colar o sistema inteiro no corpo do TCC.

---

# ANEXOS

## ANEXO A — Capturas de tela

Arquivos em `docs/fotos/` (01 a 12), conforme README do diretório.

## ANEXO B — Relatório de testes do repositório

`docs/TCC/sads_test_report.md` e `docs/TCC/diario_erros_testes_solucoes.md`.

---

# PARTE II — REFERÊNCIAS (já incluídas acima; lista consolidada ABNT)

As referências bibliográficas completas estão na seção REFERÊNCIAS da Parte I. Documentações oficiais (FastAPI, PostgreSQL, pgvector) foram usadas apenas para fundamentar características tecnológicas específicas, complementando — e não substituindo — a literatura acadêmica.

---

# PARTE III — FIGURAS/TABELAS A PRODUZIR

| ID | Descrição | Fonte sugerida |
|----|-----------|----------------|
| Figura 1 | Diagrama de contexto C4/fluxo | Redesenhar a partir de `docs/ARQUITETURA_SADS.md` |
| Figura 2 | Fluxo de recomendação | Idem |
| Figura 3 | Pipeline de agentes | `docs/TCC/apresentacao_tc1/DIAGRAMA_AGENTES.md` |
| Figura 4 | ER | `db/models.py` + SQL |
| Figura 5 | Auth sequence | `app/auth.py` |
| Figuras 6–9 | Screenshots | `docs/fotos/*.png` (já existem; inserir no editor) |
| Figura 10 | Componentes | Elaborar no Draw.io/Mermaid |
| Tabela 1–6 | Já esboçadas no texto | Ajustar formatação ABNT no Word |

---

# PARTE IV — PENDÊNCIAS FACTUAIS

- [PREENCHER: NOME COMPLETO DA AUTORA]  
- [PREENCHER: RA]  
- [PREENCHER: CAMPUS / CIDADE]  
- [PREENCHER: NOME DO ORIENTADOR]  
- [PREENCHER: MEMBROS DA BANCA]  
- [PREENCHER: DATA DA BANCA]  
- Dados editoriais completos do Guia UNIP 2025 conforme exemplar físico/PDF da autora  
- Confirmar se o grupo/coautoria deve constar na capa (repositório sugere trabalho de grupo em alguns docs)  
- Atualizar contagem de testes na versão final da banca (hoje: 146 passed, 1 failed na suíte completa)  
- Regenerar DOCX ABNT a partir deste Markdown (`scripts/md_to_docx.py` ou editor institucional)

---

# PARTE V — RASTREABILIDADE TÉCNICA

| Seção do TCC | Afirmação técnica importante | Evidência |
|--------------|------------------------------|-----------|
| 1 / 4.1 | SADS recomenda editais a partir de PDF+perfil | `routes_fase_a.evaluate`, `orchestrator.py` |
| 2.4 / 4.5 | Embeddings MiniLM 384-d + pgvector | `app/embeddings.py`, `db/init/01_extensions.sql` |
| 2.5 / ADR-003 | LLM padrão none + template | `app/llm.py`, `docs/DECISOES_ARQUITETURAIS.md` |
| 4.2 | Matriz pesos scoring v2 | `docs/scoring.md`, `agents/scoring_agent.py` |
| 4.5 | Gate 0 modernização × P&D | `agents/project_risk.py` |
| 4.5 / ADR-009 | BNDES amplo, sem linhas | `agents/sources/bndes.py`, ADR-009 |
| 4.7 | Endpoints auth e evaluate | `routes_auth.py`, `routes_fase_a.py` |
| 4.8 | PBKDF2 + HMAC | `app/auth.py` |
| 4.8 | Authz Fase A incompleta | Doc técnica + ausência de Depends nas rotas |
| 5.3 | Gabarito 10/10 documentado | `docs/TCC/sads_test_report.md` |
| 5.3 | 146 passed / 1 failed nesta execução | Saída pytest desta elaboração |
| 5.5 | Corpus piloto FINEP | ADR-006, README |

---

# PARTE VI — PREPARAÇÃO PARA A BANCA (material pessoal; fora do texto acadêmico)

| # | Pergunta difícil | Resposta recomendada | Evidência |
|---|------------------|----------------------|-----------|
| 1 | O SADS garante aprovação na FINEP? | Não. É SAD de triagem; score não é decisão do órgão. | Cap. 4 regras; UI/disclaimer docs |
| 2 | Por que pesos fixos e não AHP? | Auditabilidade no PoC; AHP ficou como futuro (ADR-004). | ADR-004, Cap. 6.4 |
| 3 | O corpus cobre todo o fomento brasileiro? | Não. Piloto FINEP (ADR-006). | ADR-006 |
| 4 | Por que BNDES não lista Finame? | Sem autorização Loja de APIs; ADR-009 trata BNDES só como opção ampla. | ADR-009, `bndes.py` |
| 5 | Vocês usam RAG de verdade? | Fluxo retrieve→generate sim; LLM off por padrão (template). | Lewis et al.; ADR-003 |
| 6 | Como a senha é armazenada? | PBKDF2-SHA256 200k + compare_digest. | `app/auth.py` |
| 7 | O isolamento multi-tenant é seguro? | Parcial: há company_id, mas falta Depends generalizado nas rotas Fase A. | Doc técnica §authz |
| 8 | Qual a dimensão do embedding? | 384 (MiniLM / hashing compatível). | schema SQL, embeddings.py |
| 9 | O que acontece em modernização sem P&D? | Gate 0 desvia de subvenção; injeta/prioriza crédito. | `project_risk.py`, Aurora test |
| 10 | Quantos testes passam? | Gabarito documentado 10/10; suíte completa nesta data 146/1. | sads_test_report; pytest |
| 11 | Por que FastAPI? | API moderna, validação Pydantic, OpenAPI nativo. | requirements, main.py |
| 12 | Há OCR? | Não; pypdf + heurísticas; RF08 parcial. | pdf_form.py |
| 13 | LangChain está no runtime? | Não; agentes próprios (ADR-002). | agents/, ADR-002 |
| 14 | Como validaram recomendações? | Gabarito de PDFs exemplo + corpus GOOD/BAD + caso Aurora. | tests/test_sads_* |
| 15 | O que falta para produção? | Authz forte, HTTPS/LGPD, corpus ampliado, usabilidade, SSO/chat. | Cap. 5–6 |

---

*Documento gerado a partir da análise integral do repositório SADS e de referências bibliográficas verificáveis. Revisar formatação ABNT (margens, espaçamento, sumário automático) no editor Word/LibreOffice conforme o Guia UNIP 2025.*
