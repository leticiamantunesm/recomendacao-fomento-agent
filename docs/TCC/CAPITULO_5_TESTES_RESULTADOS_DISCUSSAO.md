# 5 TESTES, RESULTADOS E DISCUSSÃO

Este capítulo apresenta a forma como o protótipo foi validado. A intenção não foi “provar que o sistema é perfeito”, e sim mostrar, com evidências, **onde ele acerta**, **onde falhou durante o desenvolvimento** e **o que ainda permanece aberto**. Em um trabalho de curso, essa honestidade importa: muitos dos aprendizados úteis nasceram justamente dos erros — por exemplo, quando um projeto de modernização recebia subvenção de alta tecnologia só porque o texto era semanticamente próximo do edital.

A validação combinou testes automatizados (pytest), baterias de gabarito com PDFs de exemplo, smoke manual do fluxo completo e um estudo qualitativo de comparação com assistente generativo de uso geral. Os registros detalhados estão em `docs/TCC/sads_test_report.md`, `docs/TCC/diario_erros_testes_solucoes.md` e `docs/TCC/comparacao_ias_semente_viva.md`.

## 5.1 Planejamento e estratégia de testes

Desde o início ficou claro que o risco principal do SADS não era “falhar ao abrir a tela”, e sim **recomendar o instrumento errado**. Um ranking bonito, porém inelegível, seria pior do que um ranking vazio com orientação honesta. Por isso, o planejamento privilegiou quatro frentes:

1. **Regras de elegibilidade e scoring** — pesos, hard gates, ordenação de elegíveis antes de bloqueados;
2. **Diagnóstico do projeto (Gate 0)** — distinguir P&D / risco tecnológico de modernização, aquisição ou projeto cultural;
3. **Regressão com gabarito** — PDFs classificados como “perfeitos” e “imperfeitos”, com resultado esperado explícito;
4. **Smoke manual** — ambiente, migração, atualização do corpus FINEP e caminho PDF → avaliação na interface.

Não houve, neste TCC, um plano formal de aceitação com usuários finais (questionário, SUS, amostragem). Essa ausência é limitação metodológica e será retomada na seção 5.5. Ainda assim, a estratégia adotada dialoga com a ideia de Sommerville (2011) de que testes automatizados aumentam a confiança em regressões quando o sistema evolui por incrementos — exatamente o caso do SADS, em que cada bug de demo gerava hipótese, correção e, sempre que possível, um novo teste.

**Tabela 4 — Tipos de teste e o que cada um pretende evidenciar**

| Tipo | O que valida | O que *não* valida |
|------|--------------|--------------------|
| Unitário (scoring, retrieval, embeddings, PDF) | Funções isoladas e contratos internos | Experiência do usuário na UI |
| Gabarito 01–10 / corpus v2 | Comportamento de negócio (passar, bloquear, alertar) | Retrieval vetorial live no Neon |
| Caso Aurora (BUG_01) | Modernização × crédito; parser de orçamento | Autorização server-side completa |
| Smoke manual | Caminho feliz ponta a ponta | Carga, segurança ofensiva, usabilidade formal |
| Comparação SEMENTE VIVA × Copilot | Diferença qualitativa SAD especializado × LLM geral | Superioridade estatística (n=1) |

## 5.2 Testes realizados

### 5.2.1 Suíte automatizada do repositório

A suíte concentra-se nas regras que sustentam a recomendação. Os principais arquivos e seus objetivos estão na Tabela 5.

**Tabela 5 — Arquivos de teste e objetivo**

| Arquivo | Objetivo |
|---------|----------|
| `test_scoring.py` | Pesos da matriz, critérios e ordenação elegível/inelegível |
| `test_retrieval.py` | Similaridade (cosseno) e razões de recuperação |
| `test_project_risk.py` | Gate 0 (P&D × modernização × cultural) |
| `test_instruments.py` | Taxonomia de instrumentos (subvenção, crédito, parceria…) |
| `test_finep_source.py` / `test_multi_sources.py` | Parsers de portais com fixtures HTML |
| `test_bndes_client.py` | Cliente OAuth mockado (integração *não* usada no motor — ADR-009) |
| `test_pdf_form.py` / `test_form_extraction_agent.py` | Heurísticas de extração de formulário |
| `test_embeddings.py` | Chunking e fallback hashing (384 dimensões) |
| `test_llm.py` / `test_generation_pipeline.py` | Provider `none` + geração por template |
| `test_sads_recommendations.py` | Gabarito dos 10 exemplos principais |
| `test_sads_corpus_v2.py` | Regressão GOOD/BAD (segundo corpus) |
| `test_aurora_frigorifico.py` | Caso de modernização que deve priorizar crédito |

### 5.2.2 Bateria de gabarito (exemplos 01–10)

Em 10/11/2026 foi executada a bateria documentada em `sads_test_report.md`, no ambiente Windows / Python 3.14 / pytest 8.4.2. O método foi:

1. extrair o PDF com `pypdf`;
2. montar perfil da empresa e consulta do projeto (porte, UF, TRL, orçamento, rubricas);
3. rodar Gate 0 + scoring contra editais sintéticos (um “ideal” e várias **armadilhas**, como Semicondutores FINEP, H2, Centelha MPE, FAPESP-SP e crédito PJ);
4. confrontar o obtido com o gabarito de negócio (passar / bloquear / alertar).

É importante deixar explícito o escopo: essa bateria é **offline** (sem Neon ao vivo). Ela valida o algoritmo de elegibilidade e scoring — o “cérebro” da decisão —, e não substitui um Hit@k sobre o corpus de produção.

Os dez projetos cobrem tanto casos “perfeitos” (P&D coerente, porte e UF adequados) quanto “armadilhas” deliberadas: padaria sem P&D, UF incompatível, porte grande em edital MPE, pessoa física em crédito PJ, rubricas vedadas, inconsistência orçamentária e projeto cultural.

### 5.2.3 Corpus v2 (GOOD / BAD) e caso Aurora

Além do gabarito 01–10, foi montado um segundo conjunto (GOOD_02–06 e BAD_01–06) para reforçar regressão: projetos com perfil de P&D devem permanecer elegíveis em editais coerentes; projetos ocos, de instalação sem inovação ou com marketing agressivo devem ser bloqueados ou, no mínimo, alertados.

O caso **Aurora Frigorífico (BUG_01)** nasceu de uma falha observada na própria interface: um projeto de modernização energética foi tratado de forma inconsistente (orçamento “fantasma” e ranking sem crédito). Esse tipo de evidência — *bug visto na tela, depois reproduzido em teste* — foi especialmente útil para o aprendizado do grupo, porque mostrou a distância entre “parecer inteligente” e “respeitar o instrumento certo”.

### 5.2.4 Testes manuais e operação do corpus

No diário técnico registraram-se smokes de ambiente (`check_env`), migração do banco, `refresh` FINEP e avaliação via UI. Em reload documentado (30/09/2026), o corpus piloto chegou a **31 chamadas abertas com PDF** e **31/31 embeddings** gerados — evidência de que a esteira de coleta/indexação funciona no recorte FINEP, ainda que o universo continue limitado ao piloto (ADR-006).

### 5.2.5 Estudo qualitativo SEMENTE VIVA × Copilot

Em 30/09/2026, o mesmo PDF *SEMENTE VIVA* foi avaliado no SADS (corpus FINEP indexado) e em um assistente generativo de uso geral (Microsoft Copilot), com perguntas sobre editais FINEP aderentes. O objetivo não era “vencer a IA”, e sim observar *o que cada abordagem privilegia*: aderência temática narrativa versus submetibilidade/rastreabilidade no corpus local. Os detalhes estão em `comparacao_ias_semente_viva.md` e são retomados na discussão.

## 5.3 Resultados

### 5.3.1 Evidências quantitativas da suíte

**Tabela 6 — Síntese dos resultados documentados**

| Conjunto / execução | Resultado | Fonte |
|---------------------|-----------|--------|
| Gabarito exemplos 01–10 | **10/10 PASS** (32 passed na suíte principal) | `sads_test_report.md` (10/11/2026) |
| Gate 0 (`test_project_risk`) | **7 passed** | mesmo relatório |
| Conjunto gabarito + Gate 0 | **39 passed** | mesmo relatório |
| Corpus v2 GOOD/BAD | **24 passed** | mesmo relatório |
| Regressão conjunta v1 + v2 + Gate 0 | **63 passed** | mesmo relatório |
| Suíte ampla do repositório (redação do TCC) | **146 passed, 1 failed** (`test_semente_viva_heuristic_smoke`) | execução local na elaboração |
| Reload FINEP (operação) | **31** chamadas abertas com PDF; **31/31** embeddings | diário / documentação técnica |

A falha isolada na heurística do PDF *SEMENTE VIVA* precisa ser lida com cuidado: ela aponta fragilidade da extração baseada em padrões textuais (sem OCR), e **não** derruba, por si só, os testes de scoring/recomendação que passaram no gabarito. Ainda assim, registra-se aqui de forma explícita — omitir esse detalhe enfraqueceria a credibilidade do capítulo.

### 5.3.2 O que o gabarito 01–10 mostrou na prática

**Tabela 7 — Recorte esperado × obtido (gabarito 01–10)**

| ID | Projeto (alias) | Esperado (negócio) | Obtido (síntese) | Veredito |
|----|-----------------|--------------------|------------------|----------|
| 01 | SojaResiliente AI | Passar em P&D coerente | Ideal elegível; score ≈ 89,6; tech_risk=True | PASS |
| 02 | CardioPatch IoT | Passar (saúde / Tecnova) | Ideal elegível; score ≈ 88,0 | PASS |
| 03 | Padaria Digital 4.0 | **Bloquear** subvenção (sem P&D) | tech_risk=False; 0 elegíveis; redirect crédito/Sebrae | PASS |
| 04 | NeuroGen | Alertar rubricas vedadas | Alerta de imóvel/terreno; tech_risk=True | PASS* |
| 05 | EcoPlast PR | Falhar jurisdição (PR × SP) | FAPESP-SP inelegível por região | PASS |
| 06 | AgroTitan | Falhar porte (Grande × MPE) | Centelha inelegível por porte | PASS |
| 07 | CineRaízes | Cultural; não FINEP P&D | Subvenções bloqueadas; top cultural | PASS |
| 08 | QuantumSec (PF) | Falhar PF em crédito PJ | Crédito inelegível; 0 elegíveis | PASS |
| 09 | H2V Sul | Passar (energia / H2) | Ideal elegível; score ≈ 85,1 | PASS |
| 10 | SmartLogística | Alertar orçamento / ads | Alerta math + marketing | PASS* |

\*PASS no critério mínimo do gabarito; lacuna conhecida: em 04 e 10 o sistema **alerta**, mas ainda pode listar recomendação elegível — o “kill switch” orçamentário pleno permanece como trabalho futuro.

O resultado que mais ilustra o valor do Gate 0 é o da **Padaria (03)**: antes dos hard gates, um edital de semicondutores podia aparecer no topo só por similaridade textual. Depois da correção, o sistema deixa de empurrar subvenção de alta tecnologia e sugere caminhos de modernização/crédito. Esse tipo de falso positivo era, na prática, o “medo” do grupo ao demonstrar o protótipo.

### 5.3.3 Corpus v2 e o caso Aurora

No corpus v2, os projetos GOOD (02–06) permaneceram com score ideal na faixa aproximada de **86–88** e bloquearam armadilhas de vertical incompatível. Os BAD confirmaram bloqueio de instalação solar sem P&D (BAD_02), alerta de marketing (BAD_03) e inconsistências orçamentárias (BAD_04/06). Em BAD_06, novamente aparece a lacuna: o alerta existe, mas a recomendação ainda pode sobreviver — sinal de que compliance orçamentária ainda não é hard gate completo.

No **Aurora**, a UI chegou a somar um orçamento fantasma (cerca de R$ 44,5 mi diante de um total declarado de R$ 38,4 mi), bloqueando instrumentos demais e deixando o ranking sem crédito. Após correção do parser (foco em CAPEX; interpretação de “mi” como milhões; preferência a crédito quando não há risco tecnológico), o teste automatizado passou a exigir o comportamento esperado: **subvenção bloqueada, crédito priorizado, sem falso positivo de orçamento**. O snapshot do FAIL original permanece no teste como evidência histórica (`OBSERVED_BUG`) — decisão consciente para não “apagar” o erro do relato acadêmico.

### 5.3.4 Resultado de implementação (sem confundir com satisfação)

Além dos números de pytest, o artefato **existe e opera** no recorte da Fase A: autenticação, cadastro, upload de PDF, avaliação com ranking e breakdown, histórico de applications e rotina FINEP. Isso evidencia entrega de software, mas **não** evidencia, ainda, satisfação de usuários reais — dimensão não mensurada neste trabalho.

## 5.4 Discussão

Olhando o conjunto, a principal contribuição empírica deste TCC não é um “score alto em todos os projetos”, e sim a demonstração de que **regras explícitas + regressão** conseguem corrigir falhas graves de elegibilidade que uma ordenação só semântica não corrige. Isso dialoga com a literatura de recuperação de informação, que separa a etapa de obter candidatos da etapa de ranquear com critérios (MANNING; RAGHAVAN; SCHÜTZE, 2008), e com a lógica de sistemas de apoio à decisão, em que o valor está em estruturar a escolha — não em automatizar a aprovação (TURBAN; ARONSON; LIANG, 2005; POWER, 2002).

A matriz de pesos fixos (ADR-004) mostrou-se adequada ao objetivo acadêmico: qualquer pessoa consegue auditar por que um edital subiu ou caiu. O preço dessa escolha é a ausência, ainda, de calibração formal (AHP/TOPSIS) e de métricas de ranking em produção (Hit@k). Em outras palavras, o sistema ficou mais **explicável** do que **otimizado estatisticamente** — trade-off consciente no prazo do curso.

O estudo SEMENTE VIVA × Copilot reforçou outra nuance: assistentes generativos tendem a brilhar na **narrativa temática**, enquanto o SADS depende do que está indexado e dos metadados de prazo/elegibilidade. Em mais de um caso, a API FINEP manteve situação “Aberta” mesmo com prazo de proposta vencido ou limítrofe — lembrete de que “edital aberto na API” ≠ “ainda dá tempo de submeter”. Para o produto, isso sugere evoluir o gate temporal para o campo `prazo_proposta`, e não apenas para a situação cadastral.

A tentativa de integração com APIs oficiais do BNDES também entra como resultado — ainda que negativo: sem autorização na Loja de APIs no prazo do trabalho, o motor **não** passou a detalhar linhas específicas. A ADR-009 (BNDES amplo) evita exatamente o marketing perigoso de “recomendar Finame/Cartão/Mais Inovação” sem base contratual. Academicamente, registrar a falha de autorização é tão importante quanto registrar os 10/10 do gabarito.

Por fim, os bugs corrigidos durante as rodadas (parser monetário no formato americano, falso positivo de “compra”, negação “não se aplica a P&D”, bloqueio de PF em crédito PJ, entre outros) mostram o caráter iterativo do desenvolvimento. Cada incidente do diário técnico seguiu, em geral, o mesmo ciclo: sintoma na demo → hipótese → correção mínima → teste → registro. Essa disciplina foi o que permitiu chegar ao gabarito verde sem fingir que o caminho foi linear.

## 5.5 Limitações

As limitações abaixo não invalidam o protótipo; delimitam o que se pode afirmar com segurança:

1. **Corpus piloto centrado na FINEP** — generalização para FAPs/outros órgãos é parcial (ADR-006).
2. **BNDES apenas em visão ampla** — sem catálogo oficial autorizado no motor (ADR-009).
3. **LLM externo desligado por padrão** — textos do relatório via template; chat com LLM permanece planejado.
4. **Autorização server-side incompleta** — autenticação existe; enforcement homogêneo em todas as rotas ainda não.
5. **Sem estudo formal de usabilidade** — não há amostra de usuários nem métricas de satisfação.
6. **Sem testes de carga / performance / penetração**.
7. **Hit@k e E2E contra Neon real** — não foram o eixo desta validação; o gabarito é offline no algoritmo.
8. **Extração de PDF sem OCR** — heurísticas frágeis; houve falha pontual no smoke do *SEMENTE VIVA*.
9. **Alertas orçamentários ainda não são hard gate completo** — casos 04, 10 e BAD_06 alertam corretamente, mas podem manter recomendação listada.
10. **Redirect cultural** — ainda pode sugerir caminhos genéricos de modernização em vez de priorizar só instrumentos culturais.

Em síntese: os testes sustentam que o núcleo de decisão do SADS — Gate 0, hard gates e scoring explicável — responde bem aos cenários construídos para este TCC. O que ainda falta para um produto maduro é menos “mais IA” e mais **endurecimento de compliance**, **ampliação controlada do corpus**, **autorização consistente** e **avaliação com usuários reais**.
