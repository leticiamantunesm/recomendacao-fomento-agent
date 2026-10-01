# Checklist TC1 — SADS (Canva)

## Documentos desta pasta

| Arquivo | Uso |
|---------|-----|
| `SADS_TC1_CANVA.md` | **Principal** — estrutura slide a slide para montar no Canva |
| `DIAGRAMA_AGENTES.md` | Detalhe do pipeline / contratos / chat seguro |
| `CHECKLIST_TC1.md` | Este arquivo (tempo + pendências) |
| `assets/` | Logo e capturas |
| `SADS_TC1_Apresentacao.pptx` / `_roteiro.pdf` | Versões anteriores (opcional); priorizar Canva |

## Tempo por slide

| # | Slide | Tempo |
|---|--------|------:|
| 1 | Abertura | 30 s |
| 2 | Contexto | 60 s |
| 3 | Problema | 70 s |
| 4 | Questão e objetivo | 60 s |
| 5 | Solução | 70 s |
| 6 | Protótipo | 90 s |
| 7 | **Agentes / orquestração / infra** | 90 s |
| 8 | Segurança / diferenciais / limites | 60 s |
| 9 | Próximos passos + encerramento | 50 s |
| | **Total** | **≈ 9 min 40 s** |

## Ênfases pedidas pelo professor

1. Contexto do fomento no Brasil  
2. Problema de empresas/gestores  
3. Solução SADS  
4. Funcionamento do protótipo  
5. Diferenciais técnicos → **agentes + orquestração + infra** (slide 7)  
6. Viabilidade e próximos passos (SSO, RBAC, chat LLM seguro, multi-fonte…)  

## Próximos passos a citar (roadmap — não como pronto)

- [ ] SSO / OAuth 2.0  
- [ ] Permissões personalizadas por tipo de usuário (RBAC)  
- [ ] Chat com LLM (Ollama local ou API com retenção zero; opt-in; só trechos)  
- [ ] Catálogo multi-fonte (além de FINEP)  
- [ ] Hardening de API (auth em todas as rotas de projeto)  
- [ ] AHP / TOPSIS (a validar)  
- [ ] Validação com usuários  
- [ ] Testes de segurança e documentação de limitações  

## Capturas recomendadas (Canva)

- [ ] Landing  
- [ ] Login / registro  
- [ ] Upload (`project-new`)  
- [ ] Relatório real (`project-evaluate`) com link FINEP  
- [ ] Dashboard  
- [ ] Diagrama de agentes (desenhar no Canva a partir do ASCII/Mermaid)

## Confirmar antes da banca

- [ ] Ordem de fala  
- [ ] Turma / sala / data  
- [ ] Deixar explícito: PoC FINEP ≠ catálogo nacional completo  
- [ ] Deixar explícito: sem LLM externo no PoC; chat = futuro com controles  
- [ ] Não inventar métricas de acerto  

## Revisão rápida

- [x] Estrutura lean para Canva  
- [x] Slide de agentes reforçado  
- [x] Segurança de dados / sem treino / sem LLM externo no PoC  
- [x] Próximos passos (SSO, RBAC, chat seguro, etc.)  
- [x] Sem frufru visual no documento-fonte (design fica no Canva)  
