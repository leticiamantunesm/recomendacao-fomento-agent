# SADS Landing

Landing page pública (Next.js 15 + React + Tailwind), export estático para o FastAPI servir em `/`.

## Desenvolvimento

```powershell
# Node 18+ no PATH
cd landing
npm install
npm run dev
```

Abre em http://localhost:3000

## Build de produção (export estático)

```powershell
cd landing
npm install
npm run build
```

Gera `landing/out/`. O FastAPI (`app/main.py`) serve esse diretório em `/` e monta `/_next`.

## Estrutura

```
landing/src/
  app/                 # App Router
  components/
    sections/          # Header, Hero, Problem, ...
    ui/                # Button, Section
  components/SessionRedirect.tsx
```
