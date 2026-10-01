# Banco de dados — Neon (PostgreSQL + pgvector)

O projeto usa **[Neon](https://neon.tech)** como banco padrão (Postgres gerenciado na nuvem com extensão `vector`).  
**Docker não é obrigatório.**

O arquivo `docker-compose.yml` permanece apenas como alternativa opcional, caso alguém consiga rodar Postgres localmente.

---

## Por que Neon (em vez de Docker)

| Docker local | Neon |
|--------------|------|
| Exige Docker Desktop | Só precisa de conta + internet |
| `localhost:5432` | Host `*.neon.tech` |
| Init via `db/init/*.sql` no container | Extensão criada no **SQL Editor** |
| Demo pode ser offline | Demo precisa de rede (ou compute acordado) |

No plano free, o compute do Neon pode **hibernar** (*scale to zero*). Na primeira query, aguarde alguns segundos se aparecer *“compute isn’t available yet”*.

---

## Setup (uma vez)

1. Criar projeto no [Neon Console](https://console.neon.tech)
2. Região sugerida: **AWS South America East 1 (São Paulo)**
3. Em **Connect**, copiar a `DATABASE_URL` (conexão **direta**, sem `-pooler`, para o MVP)
4. No **SQL Editor**, executar:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

5. Validar:

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

Deve retornar uma linha com `vector`.

6. No repositório:

```powershell
copy .env.example .env
```

Edite `.env` e cole **sua** URL real (não versionar esse arquivo).

---

## Variável de ambiente

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | Connection string do Neon (`sslmode=require`) |

Exemplo de formato (placeholder):

```env
DATABASE_URL=postgresql://neondb_owner:SUA_SENHA@ep-XXXX.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

Para SQLAlchemy async (T-003+), o driver pode ser `postgresql+asyncpg://...`.

**Segurança**

- Nunca commitir `.env`
- Nunca colar a senha em chat, README ou issues
- Se a senha vazou, **reset password** no Neon e atualize o `.env`

---

## Scripts SQL locais

`db/init/01_extensions.sql` documenta o mesmo `CREATE EXTENSION vector` usado no Neon.  
Com Neon, esse arquivo **não roda sozinho** — use o SQL Editor (ou um cliente `psql` apontando para a URL).

---

## Alternativa opcional: Docker

Se Docker Desktop estiver disponível:

```powershell
docker compose up -d
docker compose exec db psql -U fomento -d fomento -c "\dx"
```

Credenciais locais padrão: user/senha/db `fomento`, porta `5432`.  
Detalhes históricos no próprio `docker-compose.yml`.

---

## Troubleshooting

| Sintoma | O que fazer |
|---------|-------------|
| *compute isn’t available yet* | Esperar 30–60s e tentar de novo (cold start) |
| Falha SSL / `channel_binding` | Usar URL só com `?sslmode=require` |
| `extension "vector" does not exist` | Rodar `CREATE EXTENSION` no SQL Editor |
| Timeout na demo | Abrir o SQL Editor antes para “acordar” o compute |
