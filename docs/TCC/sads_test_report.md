# Relatório técnico — Bateria de testes SADS (exemplos_projetos)

**Data da rodada:** 10/11/2026  
**Ambiente:** Windows · Python 3.14 · pytest 8.4.2 · venv do repositório  
**Escopo:** motor de recomendação (Gate 0 + scoring com hard gates) alimentado pelos PDFs em `docs/TCC/exemplos_projetos/`  
**Comando:**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sads_recommendations.py -v
```

**Resultado da suíte:** `32 passed` (`tests/test_sads_recommendations.py`)  
**Suíte auxiliar Gate 0:** `7 passed` (`tests/test_project_risk.py`) → **39 passed** no conjunto completo.

---

## 1. Mapeamento da pasta `exemplos_projetos`

Foram encontrados **11 PDFs**. Destes, **10** são o gabarito numerado (IDs 01–10). O PDF `SEMENTE VIVA — …` é material legado/demo e **não** faz parte desta bateria.

| ID | Alias (gabarito) | Arquivo | Classificação no PDF |
|----|------------------|---------|----------------------|
| 01 | SojaResiliente AI | `AgroBioTech_Ltda.pdf` | PERFEITO |
| 02 | CardioPatch IoT | `VidaSense_Tecnologias_Médicas_SA.pdf` | PERFEITO |
| 03 | Padaria Digital 4.0 | `Pão_Quente_Comércio_de_Alimentos_Ltda.pdf` | IMPERFEITO (sem P&D) |
| 04 | NeuroGen Terapias | `NeuroGen_Biotec.pdf` | IMPERFEITO (rubricas) |
| 05 | EcoPlast Paraná | `EcoPlast_Ind_Polimeros.pdf` | IMPERFEITO (UF) |
| 06 | AgroTitan / DroneAgro | `agrotitan_sa.pdf` | IMPERFEITO (porte) |
| 07 | CineRaízes da Serra | `Produtora_Olhar_Cultural_Ltda.pdf` | PERFEITO (cultural) |
| 08 | QuantumSec Brasil | `projeto_08_Carlos_Eduardo_Silva_Pessoa_Física.pdf` | IMPERFEITO (PF/TRL) |
| 09 | H2V Sul Energia | `projeto_09_Ventos_do_Sul_Energia_SA.pdf` | PERFEITO |
| 10 | SmartLogística ERP | `projeto_10_RotaCerta_Softwares_Ltda.pdf` | IMPERFEITO (orçamento/ads) |
| — | SEMENTE VIVA | `SEMENTE VIVA — ….pdf` | Fora do gabarito 01–10 |

Metadados do gabarito: `tests/fixtures/sads_exemplos_gabarito.py`  
Loader PDF → perfil: `tests/fixtures/sads_exemplo_loader.py`  
Testes: `tests/test_sads_recommendations.py`

---

## 2. Método de teste

Cada PDF é:

1. Extraído com `pypdf`;
2. Parseado para `CompanyProfile` + `ProjectQuery` (porte, UF, TRL, orçamento, rubricas);
3. Avaliado por `diagnose_project` (Gate 0) + `ScoringAgent.score_matches` contra um conjunto de **editais sintéticos**:
   - **Ideal** (quando o gabarito prevê enquadramento);
   - **Armadilhas:** Semicondutores FINEP, H2 FINEP, Centelha MPE, FAPESP-SP, BNDES Finame PJ.

Asserções seguem o gabarito de negócios (passar / bloquear / alertar).

> Nota metodológica: a bateria é **unitário-integrada offline** (sem Neon/API live). Valida o algoritmo de elegibilidade/scoring, não o retrieval vetorial em produção.

---

## 3. Tabela comparativa — Esperado × Obtido

| ID | Projeto | Resultado esperado | Resultado obtido | Veredito |
|----|---------|--------------------|------------------|----------|
| 01 | SojaResiliente AI | Passar; ideal PIPE/Centelha | `ideal eligible=True score=89.6`; top = FAPESP PIPE/Centelha; tech_risk=True | **PASS** |
| 02 | CardioPatch IoT | Passar; Tecnova/FINEP saúde | `ideal eligible=True score=88.0`; top = Tecnova/FINEP Saúde; tech_risk=True | **PASS** |
| 03 | Padaria Digital 4.0 | Bloquear subvenção (sem risco tecnológico) | tech_risk=False; 0 elegíveis; 4 bloqueados; redirect Sebraetec + Fomento Paraná + Finame | **PASS** |
| 04 | NeuroGen | Alertar rubricas proibidas (imóvel/obra/veículo) | `forbidden=['compra de imóvel/terreno']`; tech_risk=True | **PASS** (alerta OK; ver lacuna §5) |
| 05 | EcoPlast PR | Falhar jurisdição (PR × edital SP) | FAPESP-SP → `INELEGÍVEL POR REGIÃO` | **PASS** |
| 06 | AgroTitan | Falhar porte (Grande × MPE) | Centelha → `INELEGÍVEL POR PORTE/CNPJ`; 0 elegíveis | **PASS** |
| 07 | CineRaízes | Cultural; não FINEP P&D | tech_risk=False; subvenções bloqueadas; top = ProAC/Rouanet | **PASS** |
| 08 | QuantumSec | Falhar PF em crédito PJ (+ TRL baixo) | size=PF; BNDES crédito `eligible=False`; 0 elegíveis | **PASS** |
| 09 | H2V Sul | Passar; Embrapii/FINEP energia | `ideal eligible=True score=85.1`; top = EMBRAPII/FINEP H2 | **PASS** |
| 10 | SmartLogística | Inconsistência orçamentária + ads | `math=True`; `forbidden=['marketing comercial / ads']` | **PASS** (alerta OK; ver lacuna §5) |

**Resumo:** 10/10 cenários do gabarito **passaram** nas asserções desta rodada.

---

## 4. Análise de falsos positivos / negativos

### 4.1 Onde o sistema acertou (após hard gates)

| Caso | Comportamento correto |
|------|----------------------|
| Padaria (03) | Não recomenda Semicondutores/H2/subvenção; sugere Sebraetec/crédito |
| EcoPlast (05) | UF PR bloqueia FAPESP-SP |
| AgroTitan (06) | Grande Empresa bloqueada em Centelha |
| QuantumSec (08) | PF bloqueada em Finame/subvenção/parceria |
| CineRaízes (07) | Negação “não se aplica a P&D” → sem risco tecnológico; FINEP P&D bloqueado |
| Perfeitos 01/02/09 | Ideal permanece elegível com score ≥ 60 |

### 4.2 Problemas encontrados **durante** a rodada (já corrigidos no código)

| Bug | Sintoma | Causa raiz | Correção aplicada |
|-----|---------|------------|-------------------|
| Parser monetário US | `R$ 1,200,000.00` → `None` ou `700.0` | `1,200,000.00` tratado como decimal BR | `tests/fixtures/sads_exemplo_loader.py` + `_parse_money` em `project_risk.py` |
| Gate 0 falso positivo “compra” | NeuroGen classificado como modernização | Regex `\bcompra\b` genérico | Modernização exige “compra de forno/ERP/…” |
| Gate 0 falso positivo cultural | CineRaízes com tech_risk=True | Match em “P&D” dentro de “Não se aplica a P&D” | `_RD_NEGATION` |
| Gate 0 falso negativo biotecnologia/cripto | NeuroGen/QuantumSec sem risco | Faltavam padrões `in vitro`, `síntese`, `criptograf`, etc. | Expansão de `_RD_POSITIVE` |
| PF em crédito PJ | QuantumSec poderia passar no Finame | Hard gate PF só em editais MPE | Bloqueio PF em `credito`/`subvencao`/`parceria` |

### 4.3 Lacunas remanescentes (não falharam o gabarito mínimo, mas merecem refino)

| ID | Observação | Risco |
|----|------------|-------|
| 04 NeuroGen | Rubricas vedadas **alertam**, mas o projeto ainda pode aparecer em `recommended` (ex.: FAPESP-SP) | Falso positivo parcial: alerta sem kill switch orçamentário |
| 10 SmartLogística | Ads + inconsistência matemática alertam, mas Centelha ainda pode ser recomendada | Idem — compliance orçamentária não zera elegibilidade |
| 07 CineRaízes | Redirect lista Sebraetec/Finame (útil para modernização, fraco para cultura) | UX: redirect cultural deveria priorizar ProAC/Rouanet/PNAB |
| 04 | “Veículo diretoria” às vezes não entra na lista se o texto vier só como nome de rubrica sem palavra “veículo administrativo” | Cobertura de regex de rubricas |

---

## 5. Causa raiz histórica (antes dos hard gates)

Antes da refatoração de scoring, o score era **soma ponderada pura**. Um edital com `instrument_fit ≈ 0` ainda podia ficar em #1 com ~55 pontos (similaridade alta + tema genérico + TRL neutro 70%). Isso explicava falsos positivos graves (padaria × Semicondutores).

**Mitigações já no código:**

1. Gate 0 (`agents/project_risk.py`)
2. Hard gates com cap 15% (`agents/scoring_agent.py`)
3. TRL ≥ 8 × subvenção → TRL 5%
4. Tema vertical pelo **título** do edital
5. Relatório HTML com elegíveis × bloqueados + semáforo

---

## 6. Plano de ação restante (próximas correções)

### P1 — Hard gate de compliance orçamentária
Se `ineligible_budget_items` não vazio **ou** `budget_math_inconsistency` → marcar `INELEGÍVEL POR ORÇAMENTO` e aplicar o mesmo cap 15% (como UF/porte).  
**Arquivo:** `agents/scoring_agent.py` → `_apply_hard_gates`  
**Testes:** estender 04 e 10 para `assert recommended == []` ou ideal só se rubricas forem saneadas.

### P2 — Redirect contextual por natureza
| nature | Redirect |
|--------|----------|
| modernization | Sebraetec / Finame / fomento estadual |
| cultural / audiovisual | ProAC / Rouanet / PNAB |
| pd_i | (nenhum redirect; ranking normal) |

**Arquivo:** `agents/project_risk.py` → `build_redirect_suggestions`

### P3 — Rubricas: mapear nomes de linha
Além de regex no texto corrido, classificar chaves de `budget_items` (`Veiculo Diretoria`, `Compra Terreno…`).

### P4 — Teste E2E opcional
Subir um projeto PDF via `POST /projects` + `evaluate` contra corpus Neon real e comparar Hit@k com o gabarito (fora desta rodada offline).

---

## 7. Como reproduzir

```powershell
cd "C:\Users\gpkva\OneDrive - Bayer\Desktop\recomendação_fomento_agent"
.\.venv\Scripts\Activate.ps1
python -m pytest tests/test_sads_recommendations.py tests/test_project_risk.py -v
```

Artefatos gerados:

- `tests/fixtures/_last_sads_results.json` — snapshot da última consolidação
- Este relatório: `docs/TCC/sads_test_report.md`

---

## 8. Conclusão da rodada (gabarito 01–10)

A bateria automatizada dos **10 projetos do gabarito** está verde (`32 passed` na suíte principal). O motor atual, com Gate 0 + hard gates, **elimina o falso positivo crítico da padaria em subvenção de alta tecnologia** e cobre UF, porte MPE e PF×PJ.

Os pontos que ainda merecem hardening são: **transformar alertas orçamentários (04/10) em hard gates** e **especializar o redirect cultural (07)**. Sem isso, o sistema alerta corretamente, mas ainda pode listar uma recomendação “elegível” enquanto o orçamento permanece não compliant.

---

## 9. Rodada corpus v2 (GOOD_02–06 + BAD_01–06) — 10/11/2026

**Arquivos testados (11 PDFs):**

| Key | Arquivo | Papel |
|-----|---------|-------|
| GOOD_02 | `02_REDE_FRIA_CIRCULAR.pdf` | P&D refrigeração baixo carbono |
| GOOD_03 | `03_PONTE_LEITORA.pdf` | Edtech assistiva |
| GOOD_04 | `04_AQUA_SENTINELA.pdf` | Sensores água |
| GOOD_05 | `05_ROTA_SEGURA.pdf` | Mobilidade escolar rural |
| GOOD_06 | `06_BIOFILME_PAC.pdf` | Biomaterial embalagem |
| BAD_01 | `BAD_01_CLINICA_AI.pdf` | Proposta oca (saúde/IA) |
| BAD_02 | `BAD_02_SOLAR_BAIRRO.pdf` | Instalação solar sem P&D |
| BAD_03 | `BAD_03_RECICLA_PLUS.pdf` | Marketing R$ 4,8 mi |
| BAD_04 | `BAD_04_SENSOR_CAMPO.pdf` | Orçamento inconsistente |
| BAD_05 | `BAD_05_CAPACITA_FUTURO.pdf` | Cursos sem P&D / sem orçamento |
| BAD_06 | `BAD_06_BATERIA_VERDE.pdf` | Pesquisa vaga + soma ≠ total |

**Comando:**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sads_corpus_v2.py -v
```

**Resultado:** `24 passed`  
**Regressão conjunta (v1 + v2 + project_risk):** `63 passed`

### Tabela Esperado × Obtido (corpus v2)

| Key | Alias | Esperado | Obtido | Veredito |
|-----|-------|----------|--------|----------|
| GOOD_02 | Rede Fria Circular | Passar P&D / ideal FINEP energia | tech=True; ideal **87.4**; top = FINEP Eficiência Energética | **PASS** |
| GOOD_03 | Ponte Leitora | Passar P&D / ideal edtech | tech=True; ideal **88.0** | **PASS** |
| GOOD_04 | Aqua Sentinela | Passar P&D / ideal saneamento | tech=True; ideal **87.4** | **PASS** |
| GOOD_05 | Rota Segura | Passar P&D / ideal mobilidade | tech=True; ideal **88.0** | **PASS** |
| GOOD_06 | Biofilme PAC | Passar P&D / ideal bioeconomia | tech=True; ideal **86.8** | **PASS** |
| BAD_01 | Clínica AI | Qualidade insuficiente | sem rubricas robustas; 0 elegíveis | **PASS** |
| BAD_02 | Solar Bairro | Bloquear subvenção (sem P&D) | tech=False; 0 elegíveis; redirect Sebraetec/Finame | **PASS** |
| BAD_03 | Recicla Plus | Alertar marketing | `forbidden=['marketing comercial / ads']` | **PASS** |
| BAD_04 | Sensor Campo | Inconsistência orçamentária | `budget_math=True` | **PASS** |
| BAD_05 | Capacita Futuro | Bloquear (sem P&D) | tech=False; 0 elegíveis | **PASS** |
| BAD_06 | Bateria Verde | Inconsistência orçamentária | `budget_math=True`; **ainda recomenda 2 editais** | **PASS*** |

\*PASS no critério de **alerta**; lacuna conhecida: math/rubrica ainda não aplicam kill switch (BAD_06 continua com `n_recommended=2`).

### Achados desta rodada

1. **GOOD (02–06)** passam com score ideal 86–88 e bloqueiam a armadilha de Semicondutores quando o vertical não combina.
2. **BAD_02** exigiu reforço de negação (`não apresenta adicionalidade de P&D`) + padrões de modernização (`placas solares`, `comprar equipamentos`) — senão o Gate 0 lia “desenvolvimento tecnológico” na frase negativa e liberava subvenção.
3. **BAD_03** passou após incluir `\bmarketing\b` nas rubricas vedadas.
4. **Ruído do parser:** vários GOOD marcaram `budget_math=true` por capturar números de cronograma/tabelas como rubricas — não derruba elegibilidade hoje, mas merece filtro de seção “Orçamento”.
5. **GOOD_06** gerou falso positivo leve de rubrica `compra de imóvel/terreno` (texto colateral) — investigar regex/contexto.

### Artefatos corpus v2

- `tests/test_sads_corpus_v2.py`
- `tests/fixtures/sads_corpus_v2.py`
- `tests/fixtures/_last_sads_corpus_v2.json`

---

## 10. BUG_01 — Aurora Frigorífico (modernização ≠ exige P&D) — 10/11/2026

**Arquivo:** `docs/TCC/exemplos_projetos/BUG_01_AURORA_FRIGORIFICO.pdf`  
**Teste:** `tests/test_aurora_frigorifico.py`

### O que a UI fez de errado (FAIL observado)

| Esperado | Obtido na UI | Veredito |
|----------|--------------|----------|
| Reconhecer modernização energética (sem P&D) | `tech_risk=False` + alertas de modernização | OK parcial |
| **Não** inventar “orçamento não fecha” (total R$ 38,4 mi) | Soma fantasma ≈ **R$ 44,5 mi** (custo anual + economias + `12,6 mi` lido como 12,6) | **FAIL** |
| Bloquear só **subvenção** FINEP | Bloqueou subvenção **e** zerou ranking | FAIL colateral |
| Recomendar **crédito/BNDES** (visão ampla; sem linha específica — ADR-009) | 0 elegíveis; só redirects textuais | **FAIL** |

Causa raiz:

1. Parser de rubricas misturava **custo operacional/economia** com CAPEX e lia `R$ 12,6 mi` sem escala → hard gate de orçamento matava **todos** os instrumentos (inclusive crédito).
2. Sem P&D, o motor priorizava narrativa de bloqueio e não **reordenava** preferência para `credito` — BNDES não subia no ranking mesmo quando elegível.

### Correção aplicada

- Parser: só CAPEX (`Investimento:` / rubricas nomeadas); unidade `mi` = milhões; ignora custo/economia.
- Scoring: se `has_technological_risk=False`, preferir `credito`/`parceria` e evitar `subvencao`/`pesquisa`.
- Gate de P&D continua só em `SUBVENCAO_LIKE` (não em BNDES/crédito).
- Tentativa de API oficial Developers@BNDES: **sem autorização na Loja** → BNDES permanece opção institucional ampla (ADR-009), sem Finame/Cartão/Mais Inovação como itens distintos.

### Resultado do teste automatizado

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_aurora_frigorifico.py -v
```

Esperado após correção: **PASS** (subvenção bloqueada, crédito recomendado, sem falso positivo de orçamento).  
Snapshot do bug de UI permanece documentado em `OBSERVED_BUG` no próprio teste (`verdict=FAIL`).
