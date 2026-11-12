# Decisão LLM (T-006)

## Decisão do MVP

| Item | Valor |
|------|--------|
| Provedor padrão | **`none`** |
| Motivo | Sem custo adicional de API |
| Fallback | Template local estruturado (sempre) |
| Custo | R$ 0 |

Variável de ambiente:

```env
LLM_PROVIDER=none
```

## Comportamento

```text
GenerationAgent → get_llm_client()
                      ├─ none/template  → render_template_draft()
                      ├─ ollama         → /api/generate (fallback → template)
                      └─ openai/…       → ainda não integrado → template

FormExtractionAgent → guess_form_fields() (heurística)
                   └─ se LLM_PROVIDER=ollama e campos fracos → extract_json (Ollama)
```

Com `LLM_PROVIDER=none`, o rascunho e o formulário **não** chamam rede (só heurística + template).

Código:

- `app/llm.py` — cliente + template + Ollama
- `agents/generation_agent.py` — rascunho de aderência
- `agents/form_extraction_agent.py` — formulário do projeto (PDF → campos)
- `app/pdf_form.py` — heurísticas de seção / confiança

## Ollama (opcional, local)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
FORM_EXTRACT_USE_LLM=true
```

Requer Ollama instalado e o modelo baixado (`ollama pull llama3.2`). Se o serviço estiver fora, a heurística/template continua valendo.

## O que isso NÃO é

- Não substitui banca avaliadora
- Não gera PDF final “pronto para submissão” sem revisão humana
- Não usa API paga no caminho feliz do MVP (`LLM_PROVIDER=none`)

## Smoke check

```powershell
python -c "from agents.generation_agent import GenerationAgent, DraftRequest; r=GenerationAgent().draft(DraftRequest('P','texto projeto'*20,'E','texto edital'*20)); print(r.provider, r.used_fallback); print(r.text[:200])"
```

Esperado: `provider=none`, `used_fallback=True`.
