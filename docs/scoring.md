# Scoring Agent (T-040) — funcao e desenvolvimento

## 1. Funcao do agente

O **Scoring Agent** (Agente Avaliador) recebe o resultado do **Retrieval** (ou uma lista de `EdictMatch`) e produz, para cada edital:

| Saida | Descricao |
|-------|-----------|
| `score` | Nota **0 a 100** de aderencia projeto–edital |
| `breakdown` | Pontos parciais da matriz v2 |
| `eligible` / `eligibility_flags` | Gates soft (prazo, porte, TRL, regiao) |
| `strengths` / `weaknesses` | Pontos fortes e lacunas |
| `summary` | Sintese ALTA / MEDIA / BAIXA |

Em uma frase:

> Priorizar fit estruturado (como consultoria) e usar similaridade semantica so como desempate.

---

## 2. Matriz de pesos v2

Pesos fixos (somam **1.0**):

| Criterio | Peso | Papel |
|----------|------|--------|
| Similaridade semantica | **30%** | Desempate textual (era 50%) |
| Tema / areas | **25%** | Overlap tematico |
| TRL | **15%** | Maturidade vs minimo do edital |
| Porte | **15%** | Elegibilidade de porte |
| Regiao | **10%** | UF da empresa vs regiao do edital |
| Orcamento | **5%** | Valor pedido vs faixa (quando cadastrada) |

```text
score = 0.30*sim + 0.25*area + 0.15*trl + 0.15*size + 0.10*region + 0.05*budget
```

### Gates / penalidades (alem da media ponderada)

| Condicao | Efeito |
|----------|--------|
| Prazo de proposta encerrado | `score *= 0.35` + `eligible=False` |
| Porte claramente fora | teto `score <= 45` |
| TRL muito abaixo | teto `score <= 50` |
| Regiao incompatível | teto `score <= 45` + `eligible=False` |

Ordenacao final: **elegiveis primeiro**, depois nota decrescente.

### Faixas do resumo

- **>= 75** → aderencia ALTA  
- **50–74** → aderencia MEDIA  
- **< 50** (ou inelegivel) → aderencia BAIXA / risco  

### Neutros por metadado incompleto

Sem `min_trl`, `company_sizes`, `region` ou faixa de orcamento → nota **neutra (~70)** no criterio, para nao punir corpus ainda parcial. Quando o seed enriquecer metadados, o ranking fica mais discriminativo automaticamente.

---

## 3. Pipeline

```text
CompanyProfile (size, trl, areas, uf) + ProjectQuery (text, budget_brl)
        │
        ▼
 RetrievalAgent.retrieve()  →  EdictMatch (+ region, prazo_proposta)
        │
        ▼
 ScoringAgent.score_matches()  →  ScoreReport[] ordenados
```

Arquivos:

- `agents/scoring_agent.py` — nucleo
- `scripts/score_edicts.py` — CLI
- `tests/test_scoring.py` — testes da matriz v2
- UI: `web/project-evaluate.html` (top 5 + breakdown completo)

---

## 4. CLI

```powershell
.\.venv\Scripts\Activate.ps1
$env:EMBEDDING_BACKEND="hashing"
python -m scripts.score_edicts --query "startup inovacao tecnologias digitais" --agency FINEP --k 5
```

---

## 5. DoD (T-040)

| Criterio | Status |
|----------|--------|
| Score 0–100 | Sim |
| Matriz v2 (70% estruturado / 30% semantico) | Sim |
| Breakdown (sim/tema/TRL/porte/regiao/orcamento) | Sim |
| Flags de elegibilidade | Sim |
| Feedback forcas/fraquezas | Sim |
| Integracao com Retrieval | Sim |
