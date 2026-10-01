# Guia de demonstração — SADS (TC1)

## 1. Preparação (antes da banca)

1. Neon acessível; `python -m scripts.check_env` OK.  
2. Corpus FINEP indexado (`refresh_finep_corpus` ou verificar editais com embedding).  
3. `$env:EMBEDDING_BACKEND="hashing"` se HuggingFace falhar.  
4. `uvicorn` em `127.0.0.1:8000`.  
5. Conta demo criada (empresa fictícia).  
6. PDF de projeto de teste (texto selecionável, não só scan).  
7. Aba do relatório já aberta uma vez (cache).  
8. Plano B: prints do fluxo no Canva / celular offline.

**Não** exibir `.env`, tokens ou connection string.

---

## 2. Fluxo sugerido ao vivo (≈ 4–5 min)

| Passo | Ação | O que narrar |
|-------|------|----------------|
| 1 | Abrir `/` | Landing / proposta |
| 2 | Login | Auth da organização |
| 3 | Dashboard | Multi-tenant / painel |
| 4 | Novo projeto → PDF | Entrada do SAD |
| 5 | Revisar formulário | Extração + humano no loop |
| 6 | Avaliar / relatório | Retrieval + Scoring |
| 7 | Mostrar breakdown | Explicabilidade |
| 8 | Clicar link FINEP | Ponte com fonte oficial |
| 9 | (Opcional) Aplicações | Histórico / outcome |

**Não executar ao vivo (risco):** coleta FINEP completa (lento/rede); rebuild Next; migrate em produção; demos com dados reais confidenciais.

---

## 3. Dados

| Tipo | Uso |
|------|-----|
| Empresa fictícia | Register |
| PDF fictício ou caso SEMENTE VIVA (se autorizado) | Upload |
| Editais FINEP | Públicos, já no Neon |

---

## 4. Contingência

| Falha | Ação |
|-------|------|
| API fora | Usar prints + diagrama de agentes |
| Ranking vazio | Explicar corpus; mostrar `retrieve_edicts` log pré-gravado |
| Extração fraca | Preencher formulário manualmente e reavaliar |
| Login falha | Conta backup / re-register |
| Rede FINEP | Não coletar na hora |

---

## 5. Checklist 10 minutos antes

- [ ] `/health` → ok, `llm_provider: none`  
- [ ] Login OK  
- [ ] Pelo menos 1 projeto evaluated  
- [ ] Relatório com score e link  
- [ ] Canva aberto no slide certo  
- [ ] Quem fala o quê definido  

---

## 6. Frase se algo quebrar

> “O fluxo completo está documentado e foi validado em desenvolvimento; neste momento a dependência X falhou — o diagrama mostra Retrieval e Scoring sobre o corpus FINEP, que é o núcleo da recomendação.”
