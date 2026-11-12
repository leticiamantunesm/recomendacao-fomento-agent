# Corpus e Agente Coletor (FINEP + FAPESP + Embrapii + BNDES)

## Objetivo

Buscar chamadas na **FINEP** (API + PDFs) e, em paralelo, na **FAPESP**, **Embrapii** e **BNDES** (detalhe + anexos), guardar metadados e alimentar o Neon para a UI.

Piloto validado do TCC continua sendo **FINEP**; FAPESP, Embrapii e BNDES estão em **paridade parcial**.

Portal humano FINEP: [Oportunidades Finep](https://www.finep.gov.br/oportunidades) · chamadas publicas.  
Portal FAPESP: [Chamadas de Propostas](https://fapesp.br/chamadas/).  
Portal Embrapii: [Transparência — Chamadas Públicas](https://embrapii.org.br/transparencia/#chamadas).  
Portal BNDES: [Navegador de Financiamentos](https://www.bndes.gov.br/wps/portal/site/home/financiamento/navegador/#!/).

API usada:

- `GET /o/c/chamadapublicas`
- `GET /o/c/chamadapublicas/{id}?nestedFields=documentos`

## O que o coletor ampliado captura

| Campo | Origem |
|-------|--------|
| Titulo, situacao, temas | API list/detail |
| Tipo de oportunidade, regiao, publico, cooperacao, contrapartida | API detail |
| Vigencia / prazo proposta | API detail |
| Descricao (texto) | `descricaoRawText` |
| PDFs (edital, regulamento, anexos, faq…) | `documentos` |

Arquivos:

- PDFs → `data/raw_pdfs/finep_<id>_*.pdf`
- Metadados JSON → `data/outputs/finep_metadata/<id>.json`
- Manifest **so FINEP** → `data/corpus_manifest.csv` (default)
- Log → `data/outputs/finep_collect_log.json`

## Como rodar

### Pipeline completo (recomendado para a UI)

```powershell
$env:EMBEDDING_BACKEND="hashing"
.\.venv\Scripts\python.exe -m scripts.refresh_finep_corpus --limit 20
```

Isso faz: coleta (+anexos) → extract → `seed --agency FINEP --purge-other` → `index --reindex`.

### FINEP + FAPESP + Embrapii + BNDES (sem apagar outras agências)

```powershell
$env:EMBEDDING_BACKEND="hashing"
.\.venv\Scripts\python.exe -m scripts.refresh_finep_corpus --source finep,fapesp,embrapii,bndes --limit 10
```

Com mais de uma fonte, o seed **não** usa `--purge-other` (preserva o que já está no Neon).

### So coleta

```powershell
.\.venv\Scripts\python.exe -m scripts.collect_editais --source finep --limit 20 --situacao aberta --extract
.\.venv\Scripts\python.exe -m scripts.collect_editais --source fapesp --limit 10 --extract
.\.venv\Scripts\python.exe -m scripts.collect_editais --source embrapii --limit 10 --extract
.\.venv\Scripts\python.exe -m scripts.collect_editais --source bndes --limit 10 --extract
```

| Flag | Efeito |
|------|--------|
| `--limit N` | Maximo de **chamadas** com PDF |
| `--situacao aberta\|todas\|encerrada` | Filtro |
| `--anexos` / `--no-anexos` | Todos os PDFs vs so o primario |
| `--finep-only-manifest` | Manifest so FINEP (default) |
| `--extract` | Gera `data/texts/*.txt` |

### Seed FINEP-only

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_corpus --agency FINEP --purge-other
```

O seed junta: descricao da API + texto do edital + anexos no `edicts.raw_text`, e grava metadados em `edicts.metadata`.

## Codigo

- `agents/sources/finep.py` — cliente ampliado
- `agents/sources/fapesp.py` — listagem + detalhe (meta-refresh) + anexos
- `agents/sources/embrapii.py` — transparência `#chamadas` + detalhe + PDFs (GCS/wp-content)
- `agents/sources/bndes.py` — API `/apoioFinanceiro/rest/linhasProgramas` + detalhe produto + PDFs
- `agents/scraper_agent.py` — orquestracao + manifest
- `scripts/collect_editais.py` — CLI coleta
- `scripts/refresh_finep_corpus.py` — E2E refresh
- `scripts/seed_corpus.py` — seed com purge

## Limitacoes

- Layout/API FINEP pode mudar
- Nem toda oportunidade do hub `/oportunidades` e chamada publica com PDF
- FAPESP: anexos frequentemente DOCX (baixados; texto principal vem do HTML da chamada); PDFs externos variam
- Embrapii: listagem em [transparencia/#chamadas](https://embrapii.org.br/transparencia/#chamadas); PDFs em `storage.googleapis.com` / `wp-content`; areas de atuacao entram como fluxo continuo
- BNDES: Navegador é SPA; coleta via API REST + páginas de produto; filtro default `innovation_only` (~linhas de inovação); fallback curado se API cair
- Rede corporativa precisa liberar `finep.gov.br`, `fapesp.br`, `embrapii.org.br` e `bndes.gov.br`
- Boletim/e-book manuais saem do manifest no refresh FINEP-only (podem voltar com `--no-finep-only-manifest` se necessario)
