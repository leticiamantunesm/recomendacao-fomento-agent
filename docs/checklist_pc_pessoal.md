# Checklist — ambiente de desenvolvimento (Neon + GitHub)

Objetivo: clonar o projeto, configurar o banco **Neon** (sem Docker) e, quando o código existir, executar API/agentes/front.

Legenda: `[ ]` pendente · `[x]` feito

---

## A) Contas e ferramentas base

- [ ] Conta GitHub com acesso ao repo  
  `https://github.com/leticiamantunesm/recomendacao-fomento-agent`
- [ ] [Git](https://git-scm.com/download/win) instalado (`git --version`)
- [ ] Conta [Neon](https://console.neon.tech) com projeto Postgres criado
- [ ] (Recomendado) [Cursor](https://cursor.com) no PC onde você desenvolve/testa
- [ ] (T-003+) Python 3.10+ (`python --version`)
- [ ] Internet disponível ao testar o banco (Neon é nuvem)

**Docker:** opcional. Não é necessário para o fluxo padrão do TCC.

---

## B) Clonar o projeto

```powershell
mkdir C:\dev -Force
cd C:\dev
git clone https://github.com/leticiamantunesm/recomendacao-fomento-agent.git
cd recomendacao-fomento-agent
```

- [ ] Clone concluído
- [ ] Pastas `app/`, `agents/`, `db/`, `.env.example` visíveis
- [ ] `git status` funciona sem erro

> Fonte da verdade: **GitHub**. Evite misturar só OneDrive como “ambiente oficial”.

---

## C) Validar banco — Neon + pgvector

1. No Neon Console → **Connect** → copiar `DATABASE_URL` (direta, sem `-pooler`)
2. **SQL Editor** → já deve ter rodado:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

- [ ] Resultado mostra `vector`
- [ ] No repo:

```powershell
copy .env.example .env
```

- [ ] `.env` preenchido com a URL real (arquivo **não** commitado)
- [ ] Senha **não** aparece em README, chat ou GitHub

Detalhes: [`docs/database.md`](database.md).

---

## D) Sincronizar código (dia a dia)

### Depois de editar

```powershell
git add .
git status
git commit -m "mensagem clara do que mudou"
git push
```

### Antes de testar em outro PC

```powershell
git pull
```

- [ ] Conferir se o `.env` local ainda existe nesse PC (não vem pelo Git)

---

## E) T-003 — Python e dependências

Guia: [`dev_setup.md`](dev_setup.md)

- [ ] Python 3.10–3.12 recomendado (`python --version`)
- [ ] `python -m venv .venv` + Activate
- [ ] `pip install -r requirements.txt`
- [ ] `.env` com `DATABASE_URL` real do Neon
- [ ] `python -m scripts.check_env` → OK
- [ ] (Opcional) `uvicorn app.main:app --reload` e abrir `/health`

---

## F) Quando existirem os agentes do TCC

| Necessidade | Por quê |
|-------------|---------|
| Código atualizado (`git pull`) | Evitar versão antiga |
| Neon acessível (rede + compute ativo) | Indexador/retrieval usam `pgvector` |
| Dependências Python | FastAPI, sentence-transformers, etc. |
| Corpus em `data/` (quando houver) | Demo de retrieval |
| LLM ou fallback | Geração de rascunho |

Checklist de execução (futuro):

- [ ] Neon “acordado” (abrir SQL Editor se estiver hibernando)
- [ ] API sobe (comando do README)
- [ ] `GET /health` ok
- [ ] Pipeline de teste roda
- [ ] Front (se houver) em `localhost` neste PC

---

## G) O que NÃO vem pelo GitHub

- [ ] Agent do Cursor (chat) — é o app Cursor
- [ ] Histórico de chats de outro PC
- [ ] Arquivo `.env` e senhas
- [ ] PDFs grandes em `data/` (em geral ignorados pelo git)

---

## H) Ritual mínimo antes da demo (fim de setembro)

- [ ] Internet ok
- [ ] `git pull`
- [ ] Neon Active (SQL Editor responde; `vector` ok)
- [ ] `.env` correto neste PC
- [ ] API/front sobem
- [ ] Ensaio E2E 1×
- [ ] Plano B: vídeo se rede/LLM falhar

---

## Ordem sugerida

1. **A** + **B** (contas + clone)  
2. **C** (Neon + `vector` + `.env`) — banco pronto  
3. **D** (push/pull)  
4. **T-003** e seções **E/F**

---

## Socorro rápido (Neon)

| Problema | Ação |
|----------|------|
| *compute isn’t available yet* | Esperar 30–60s, atualizar, tentar de novo |
| Extensão sumiu | Rodar de novo `CREATE EXTENSION IF NOT EXISTS vector;` |
| Senha vazou | Reset password no Neon + atualizar `.env` |
| App não conecta | Conferir `sslmode=require`; testar sem `channel_binding` |
