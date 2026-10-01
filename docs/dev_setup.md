# Ambiente Python — T-003

## Pré-requisitos

- Python **3.10, 3.11 ou 3.12** (recomendado).  
  Python 3.13/3.14 pode falhar na instalação de `torch` / `sentence-transformers`.
- Conta Neon + `DATABASE_URL` no arquivo `.env` (ver [`database.md`](database.md))

Verifique a versão:

```powershell
python --version
```

---

## 1. Criar ambiente virtual

Na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Se o PowerShell bloquear o script de ativação:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 2. Instalar dependências

```powershell
pip install -r requirements.txt
```

Para testes:

```powershell
pip install -r requirements-dev.txt
```

A primeira instalação baixa PyTorch (pode demorar vários minutos).

---

## 3. Configurar `.env`

```powershell
copy .env.example .env
```

Edite `.env` e cole a `DATABASE_URL` real do Neon (**não** commitir).

---

## 4. Validar (DoD da T-003)

```powershell
python -m scripts.check_env
```

Deve imprimir `T-003 smoke check: OK`.

Testes unitários da Settings:

```powershell
pytest tests/test_config.py -q
```

Subir a API mínima:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

No navegador ou outro terminal: http://127.0.0.1:8000/health  
Swagger: http://127.0.0.1:8000/docs

---

## Pacotes principais

| Pacote | Uso |
|--------|-----|
| `fastapi` / `uvicorn` | API |
| `sqlalchemy` / `asyncpg` | Postgres (Neon) |
| `pydantic-settings` | Config central (`app/config.py`) |
| `pypdf` | Extração de PDF |
| `httpx` | HTTP cliente |
| `sentence-transformers` | Embeddings locais |

---

## Problemas comuns

| Sintoma | Ação |
|---------|------|
| `torch` / `sentence-transformers` não instala | Use Python 3.12 (`py -3.12 -m venv .venv`) |
| `ModuleNotFoundError: app` | Rode os comandos na **raiz** do repo, com venv ativo |
| `/health` mostra host `ep-XXXX...` | Ainda está o placeholder do `.env.example` — cole a URL real |
| Senha no Git | Confirme que `.env` está no `.gitignore` |
