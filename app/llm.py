"""Camada LLM modular (T-006) — padrão: none + fallback por template (custo zero)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.config import Settings, get_settings


@dataclass
class GenerationResult:
    text: str
    provider: str
    used_fallback: bool
    notes: str = ""


class LLMClient(Protocol):
    def generate(
        self,
        *,
        task: str,
        project_excerpt: str,
        edict_excerpt: str,
        extra: dict[str, Any] | None = None,
    ) -> GenerationResult: ...


def _clip(text: str, max_chars: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def render_template_draft(
    *,
    project_excerpt: str,
    edict_excerpt: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """Rascunho estruturado sem chamar API paga (fallback oficial do MVP)."""
    extra = extra or {}
    project_title = str(extra.get("project_title") or "Projeto da empresa")
    edict_title = str(extra.get("edict_title") or "Edital selecionado")
    company_name = str(extra.get("company_name") or "Empresa proponente")

    return f"""# Rascunho de aderência (modo template — LLM_PROVIDER=none)

## 1. Identificação
- Empresa: {company_name}
- Projeto: {project_title}
- Edital de referência: {edict_title}

## 2. Resumo do projeto (trechos)
{_clip(project_excerpt)}

## 3. Requisitos / foco do edital (trechos)
{_clip(edict_excerpt)}

## 4. Objetivos sugeridos (a revisar)
1. Alinhar o escopo técnico do projeto aos eixos temáticos do edital.
2. Evidenciar maturidade tecnológica (TRL), equipe e contrapartidas exigidas.
3. Descrever entregáveis, cronograma e indicadores de resultado compatíveis com a chamada.

## 5. Justificativa de aderência (rascunho)
O projeto apresenta sobreposição temática com o edital indicado. Os trechos acima devem ser
revisados pela equipe para confirmar elegibilidade (porte, TRL, despesas elegíveis e prazos).
Este texto foi gerado por template local (sem custo de API) e não substitui análise humana.

## 6. Próximos passos
- Completar seções obrigatórias do formulário da Finep/órgão.
- Anexar comprovações e orçamento conforme regulamento.
- Revisar prazos de submissão na página oficial da chamada.

---
_Gerado automaticamente pelo fallback de template (T-006)._
"""


class NoneLLMClient:
    """Provedor oficial do MVP: não chama rede; sempre usa template."""

    provider_name = "none"

    def generate(
        self,
        *,
        task: str,
        project_excerpt: str,
        edict_excerpt: str,
        extra: dict[str, Any] | None = None,
    ) -> GenerationResult:
        text = render_template_draft(
            project_excerpt=project_excerpt,
            edict_excerpt=edict_excerpt,
            extra=extra,
        )
        return GenerationResult(
            text=text,
            provider=self.provider_name,
            used_fallback=True,
            notes=f"task={task}; template local sem custo de API",
        )


class PassthroughFallbackClient:
    """Para provedores futuros (ollama/openai): se indisponíveis, cai no template."""

    def __init__(self, requested: str) -> None:
        self.requested = requested
        self._fallback = NoneLLMClient()

    def generate(
        self,
        *,
        task: str,
        project_excerpt: str,
        edict_excerpt: str,
        extra: dict[str, Any] | None = None,
    ) -> GenerationResult:
        result = self._fallback.generate(
            task=task,
            project_excerpt=project_excerpt,
            edict_excerpt=edict_excerpt,
            extra=extra,
        )
        result.provider = self.requested
        result.used_fallback = True
        result.notes = (
            f"Provedor '{self.requested}' ainda não integrado neste MVP; "
            "usando fallback template (T-006)."
        )
        return result


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    settings = settings or get_settings()
    provider = (settings.llm_provider or "none").strip().lower()
    if provider in {"none", "template", "off", "disabled"}:
        return NoneLLMClient()
    # Espaço reservado para ollama/openai/anthropic sem custo obrigatório no MVP
    return PassthroughFallbackClient(provider)
