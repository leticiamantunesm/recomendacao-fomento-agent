# Corpus e Agente Coletor (FINEP ampliado)

## Objetivo

Buscar chamadas na **FINEP**, baixar **edital + anexos**, guardar **metadados ricos** e alimentar o Neon para a UI ranquear só corpus **FINEP fresco**.

Portal humano: [Oportunidades Finep](https://www.finep.gov.br/oportunidades) · chamadas publicas.

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

### So coleta

```powershell
.\.venv\Scripts\python.exe -m scripts.collect_editais --source finep --limit 20 --situacao aberta --extract
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
- `agents/scraper_agent.py` — orquestracao + manifest
- `scripts/collect_editais.py` — CLI coleta
- `scripts/refresh_finep_corpus.py` — E2E refresh
- `scripts/seed_corpus.py` — seed com purge

## Limitacoes

- Layout/API FINEP pode mudar
- Nem toda oportunidade do hub `/oportunidades` e chamada publica com PDF
- Rede corporativa precisa liberar `finep.gov.br`
- Boletim/e-book manuais saem do manifest no refresh FINEP-only (podem voltar com `--no-finep-only-manifest` se necessario)
