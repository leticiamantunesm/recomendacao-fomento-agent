# Testes e comparação com outras IAs (estudo de caso SEMENTE VIVA)

**Projeto:** Sistema de Agentes de IA para Gestão e Subvenção de Editais (FomentoAgent)  
**Finalidade:** evidência experimental para o TCC — avaliação qualitativa frente a assistentes generativos de uso geral  
**Data do experimento:** 30/09/2026  
**Projeto-alvo:** *SEMENTE VIVA — Plataforma de Visão Computacional de Baixo Custo para Seleção de Sementes na Agricultura Familiar*  
**Documento-fonte:** `docs/TCC/exemplos_projetos/SEMENTE VIVA — … Agricultura Familiar.pdf`

---

## 1. Objetivo do experimento

Comparar a recomendação de editais FINEP produzida por:

| Sistema | Tipo |
|---------|------|
| **FomentoAgent** (protótipo do TCC) | Pipeline retrieval + scoring sobre corpus FINEP indexado (situação *Aberta*) |
| **Microsoft Copilot** (chat M365 / web) | LLM generalista com busca/web + leitura do PDF |

Pergunta de pesquisa (operacional):

> Dado o mesmo projeto, as IAs generalistas e o sistema especializado convergem no ranking? Quando divergem, o que prevalece — **aderência temática** ou **viabilidade temporal/elegibilidade**?

---

## 2. Protocolo de teste

### 2.1 Entrada comum

- PDF completo do SEMENTE VIVA (proposta simulada, dados fictícios, set/2026).
- Enquadramento declarado no próprio PDF:  
  *MCTI/FINEP/FNDCT — Subvenção Econômica à Inovação: Desafios Tecnológicos para Agricultura Familiar*.
- Perfil implícito: empresa (Raiz Clara), parceria ICT (IFNMG) + cooperativas, TRL 4→7, orçamento ~R$ 2,4 mi, foco agricultura familiar + visão computacional.

### 2.2 Procedimento FomentoAgent

1. Cadastro de empresa/funcionário na UI Fase A.  
2. Upload do PDF em **Novo projeto** (ou Materiais tipo Projeto).  
3. Revisão do formulário extraído.  
4. Avaliação automática → top 5 (`agency=FINEP`, matriz de scoring v2).  
5. Registro do ranking e dos critérios exibidos na tela de resultado.

### 2.3 Procedimento Copilot

1. Upload / contexto do mesmo PDF.  
2. Perguntas sucessivas (resumo das usadas no experimento):  
   - *Pensando nos editais abertos da FINEP, qual mecanismo de fomento faz mais sentido?*  
   - *Quais chamadas da FINEP especificamente?*  
   - *E o Proninc 2026?*  
3. Registro do ranking textual e das justificativas.

### 2.4 Critérios de comparação

| Critério | Descrição |
|----------|-----------|
| C1 Aderência temática | Agricultura familiar, digital, baixo custo, P&D |
| C2 Tipo de proponente | Empresa vs ICT vs cooperativa |
| C3 Instrumento | Subvenção empresarial vs incubação/economia solidária vs crédito |
| C4 **Prazo / submetibilidade** | `prazo_proposta` ainda válido na data do teste |
| C5 Rastreabilidade | ID FINEP / URL / metadado verificável |
| C6 Explicabilidade | Breakdown de critérios vs prosa persuasiva |

---

## 3. Corpus FINEP relevante (estado em 30/09/2026)

Fonte: `data/corpus_manifest.csv` + `data/outputs/finep_metadata/*.json` após `refresh_finep_corpus --all` (31 chamadas com situação *Aberta* na API).

| ID interno | Título (curto) | Público (meta) | `prazo_proposta` | Status no teste (30/09/2026) |
|------------|----------------|----------------|------------------|------------------------------|
| `finep-754098` | Desafios Tecnológicos para Agricultura Familiar (subvenção) | Cooperativa* / texto fala em **empresas** | **não preenchido** no metadado | Situação API: Aberta; prazo real **incerto** no cadastro |
| `finep-755892` | AgriFam-ICT 2026 (cadeias socioprodutivas p/ ICTs) | **ICT** | **2026-07-03** | **Prazo vencido** (~3 meses) |
| `finep-754839` | Mais Inovação – Cadeias Agroindustriais | Subvenção (empresas) | **2026-09-30** | **Limítrofe / encerrado no dia do teste** |
| `finep-958302` | Tecnova 2026/2027 (carta-convite a **agentes**) | Agentes estaduais | **2026-08-03** | **Prazo vencido** |
| `finep-1057230` | **Proninc / 2026** | **ICT** + ITCP/NIT | **2027-01-14** | **Dentro do prazo** |

\*Metadado FINEP lista `Cooperativa`; a descrição do edital enfatiza subvenção a empresas brasileiras — ruído típico de cadastro.

**Observação crítica:** a API FINEP pode manter `situacao = Aberta` mesmo após o fim do prazo de propostas. Por isso, filtrar só por “Aberta” **não** garante submetibilidade. O campo `prazo_proposta` é o gate temporal correto.

---

## 4. Resultados

### 4.1 Ranking FomentoAgent (síntese do experimento)

Na avaliação do SEMENTE VIVA, o sistema destacou, entre outras, a chamada:

1. **Programa Nacional de Incubadoras Tecnológicas de Cooperativas Populares (Proninc) / 2026** (`finep-1057230`)

**Por que o algoritmo favorece esse resultado (hipótese confirmada pelo desenho do scoring):**

- Forte sobreposição lexical/semântica: cooperativas, agricultura familiar, soberania alimentar, sistemas digitais, inclusão produtiva.  
- `prazo_proposta` ainda válido → não sofre penalidade temporal.  
- Corpus limitado às chamadas marcadas *Aberta*; ranking por similaridade + matriz v2 **sem gate rígido** de tipo de proponente (ICT vs empresa).  
- Orçamento do projeto (~R$ 2,4 mi) cai na faixa textual do Proninc (R$ 2–5 mi), reforçando a impressão de encaixe.

**Limitação:** o Proninc exige ICT + ITCP/NIT como eixo executivo; o SEMENTE VIVA está redigido como **subvenção empresarial de P&D**. Aderência temática ≠ elegibilidade plena.

### 4.2 Ranking Copilot (síntese do diálogo)

Ordem típica defendida pelo Copilot:

1. **Subvenção Econômica FINEP – Agricultura Familiar / AgriFam** (soluções digitais para pequena propriedade) — aderência estimada ~90–95%  
2. Cadeias socioprodutivas / sistemas agroalimentares  
3. Tecnova (se MPE)  
4. EMBRAPII (fora FINEP pura)  
5. Proninc como **opção secundária** (~70%), exigindo reposicionamento para inovação social  

Ao ser confrontado com o Proninc, o Copilot alinhou-se à análise de consultoria: bom encaixe social/territorial, mas **linguagem do PDF é de subvenção tecnológica empresarial**.

### 4.3 Achado central — melhor encaixe temático, mas fora do prazo

| Achado | Detalhe |
|--------|---------|
| **Copilot acertou o mecanismo** | Priorizou subvenção econômica ligada à agricultura familiar / digital rural — coerente com o texto do SEMENTE VIVA e com `finep-754098` / família AgriFam. |
| **Copilot falhou no prazo** | A chamada **AgriFam-ICT (`finep-755892`)** — a mais próxima do discurso “AgriFam / soluções digitais” no corpus — tem `prazo_proposta = 03/07/2026`, **já vencido** na data do teste (30/09/2026). Tecnova agentes (`958302`) também vencido (03/08/2026). |
| **FomentoAgent acertou a janela temporal** | Proninc permanece submetível até **14/01/2027** (segundo metadado coletado). |
| **FomentoAgent falhou no enquadramento ideal** | Elevou Proninc sem filtrar proponente ICT-only nem distinguir “melhor tema vencido” de “melhor tema ainda aberto”. |

Em uma frase para a banca:

> O assistente generalista recomendou o **enquadramento temático mais plausível**, porém ancorado em chamada(s) **já fora do prazo de submissão**; o protótipo especializado, ao operar sobre corpus *Aberta* com prazo ainda válido, recomendou uma chamada **ainda aberta**, porém de **elegibilidade institucional distinta** (Proninc/ICT).

---

## 5. Tabela comparativa (visão sintética)

| Dimensão | FomentoAgent | Copilot |
|----------|--------------|---------|
| Fonte de editais | Corpus indexado (31 FINEP *Aberta*) | Conhecimento + web/PDF; nem sempre amarra ID/prazo |
| Top-1 no caso | Proninc 2026 | “AgriFam / Subvenção AF” |
| Aderência temática (SEMENTE VIVA) | Média–alta (cooperativas/AF) | **Alta** (subvenção P&D AF) |
| Prazo do top-1 | **Válido** (até 14/01/2027) | **Vencido** (AgriFam-ICT 03/07/2026) se mapeado ao corpus |
| Tipo de proponente | Não gated | Discutido em prosa, sem bloqueio formal |
| Breakdown auditável | Sim (matriz v2) | Não (texto persuasivo) |
| Hit@k formal | Ainda qualitativo neste caso | Não aplicável |
| Risco para o usuário | Submeter no instrumento errado | Perder tempo em edital encerrado |

---

## 6. Discussão para o TCC

### 6.1 Dois tipos de erro (úteis na monografia)

1. **Erro de elegibilidade temporal (Copilot):** recomenda o “melhor edital de ontem”.  
2. **Erro de elegibilidade institucional (FomentoAgent):** recomenda o “melhor texto ainda aberto”, mesmo com público-alvo ICT.

Ambos são falhas de *decision support*; o valor do protótipo está em tornar o segundo tipo **corrigível** com metadados (`target_audience`, `prazo_proposta`, instrumento) — enquanto o primeiro exige **fonte viva + checagem de prazo**, que IAs generalistas frequentemente omitem.

### 6.2 Por que a API “Aberta” engana

No metadado coletado, AgriFam-ICT segue `situacao: Aberta` com prazo já passado. Isso explica:

- presença no corpus do FomentoAgent;  
- possível confusão de qualquer LLM que leia só o rótulo “aberta” em páginas FINEP.

**Implicação de método:** o pipeline deve tratar `prazo_proposta < now` como **inelegível** (gate), independentemente de `situacao`.

### 6.3 Ground truth provisório deste caso

Para o SEMENTE VIVA **na data 30/09/2026**:

| Prioridade consultoria | Chamada | Observação |
|------------------------|---------|------------|
| Ideal temático | Desafios AF / AgriFam (família) | Verificar se ainda há prazo real em `754098`; AgriFam-ICT **já fechou** |
| Aberto + relacionado | Proninc | Só com reescrita ICT/ITCP |
| Aberto + empresarial agro | Cadeias Agroindustriais (`754839`) | Prazo no próprio dia do teste — validar hora/resultado FINEP |
| Evitar como “submissão MPE” | Tecnova carta-convite | É seleção de agentes, prazo vencido |

---

## 7. Métricas sugeridas para ampliar o estudo

Repetir o protocolo com N≥3 projetos exemplo e anotar:

| Métrica | Definição |
|---------|-----------|
| **Temporal-OK@1** | Top-1 com `prazo_proposta ≥ data do teste` |
| **Proponent-OK@1** | Top-1 compatível com tipo do proponente (empresa/ICT) |
| **Theme-OK@3** | Pelo menos 1 dos top-3 na família temática anotada |
| **Deadline hallucination rate** (LLM) | Fração de recomendações cujo prazo já havia encerrado |
| Concordância ordinal | Spearman entre ranking FomentoAgent e ranking do avaliador humano |

Sistemas a incluir em rodadas futuras: ChatGPT, Gemini, Claude (mesmo PDF + mesma pergunta), sempre na **mesma data** (prazos mudam).

---

## 8. Conclusões do experimento

1. **Sim, o Copilot apontou um programa de melhor aderência temática** à narrativa do SEMENTE VIVA (subvenção / agricultura familiar / digital).  
2. **Esse enquadramento, no corpus FINEP coletado, corresponde a chamada(s) com prazo vencido** (notadamente AgriFam-ICT em 03/07/2026; Tecnova agentes em 03/08/2026).  
3. **O FomentoAgent priorizou Proninc**, ainda **dentro do prazo**, mas com **elegibilidade ICT** — divergência esperada na ausência de gate de proponente.  
4. Para o TCC, o caso ilustra a tese do produto:  
   *IA generalista otimiza persuasão temática; sistema especializado deve otimizar **submetibilidade** (prazo + elegibilidade + tema).*  
5. Próximo incremento técnico recomendado:  
   - gate duro `prazo_proposta`;  
   - peso/gate `target_audience`;  
   - exibir na UI “vencido / aberto / prazo nulo”;  
   - não listar como recomendação primária editais com prazo expirado mesmo se `situacao=Aberta`.

---

## 9. Anexos

### 9.1 Prompt-base sugerido (replicação)

```text
Com base no PDF anexo (SEMENTE VIVA), liste as 5 chamadas FINEP mais aderentes
que ainda aceitem proposta HOJE. Para cada uma informe: nome oficial, URL ou ID,
público elegível, prazo de submissão e se o proponente empresa (não ICT) pode
submeter. Não recomende editais com prazo vencido.
```

### 9.2 Referências internas do repositório

- Corpus: `data/corpus_manifest.csv`  
- Metadados: `data/outputs/finep_metadata/{1057230,755892,754098,958302,754839}.json`  
- Scoring: `docs/scoring.md`, `agents/scoring_agent.py`  
- Diário de erros: `docs/TCC/diario_erros_testes_solucoes.md`  
- Projeto exemplo: `docs/TCC/exemplos_projetos/`

### 9.3 Histórico

| Data | Evento |
|------|--------|
| 30/09/2026 | Experimento SEMENTE VIVA · FomentoAgent vs Copilot · documento criado |

*Documento vivo: novas rodadas com outras IAs devem ser acrescentadas na seção 4 com a mesma tabela de prazos na data do teste.*
