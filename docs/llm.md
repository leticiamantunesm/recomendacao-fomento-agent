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
                      └─ ollama/openai… → (não integrado no MVP) → mesmo template
```

O rascunho monta seções (resumo, trechos do edital/projeto, objetivos, próximos passos) **sem** chamar rede.

Código:

- `app/llm.py` — cliente + template
- `agents/generation_agent.py` — agente de geração

## O que isso NÃO é

- Não substitui banca avaliadora
- Não gera PDF final “pronto para submissão” sem revisão humana
- Não usa OpenAI/Anthropic/Ollama no caminho feliz do MVP

## Evolução futura (opcional, fora do custo zero)

1. Implementar cliente Ollama local (`LLM_PROVIDER=ollama`)
2. Manter template como fallback se Ollama/API falhar
3. Nunca commitar chaves de API

## Smoke check

```powershell
python -c "from agents.generation_agent import GenerationAgent, DraftRequest; r=GenerationAgent().draft(DraftRequest('P','texto projeto'*20,'E','texto edital'*20)); print(r.provider, r.used_fallback); print(r.text[:200])"
```

Esperado: `provider=none`, `used_fallback=True`.
