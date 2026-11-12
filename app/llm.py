"""Camada LLM modular (T-006) — padrão: none + fallback; Ollama opcional."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.config import Settings, get_settings


@dataclass
class GenerationResult:
    text: str
    provider: str
    used_fallback: bool
    notes: str = ""


@dataclass
class StructuredExtractResult:
    data: dict[str, Any]
    provider: str
    used_fallback: bool
    notes: str = ""
    raw_text: str = ""


class LLMClient(Protocol):
    def generate(
        self,
        *,
        task: str,
        project_excerpt: str,
        edict_excerpt: str,
        extra: dict[str, Any] | None = None,
    ) -> GenerationResult: ...

    def extract_json(
        self,
        *,
        task: str,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
    ) -> StructuredExtractResult: ...


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


def parse_json_payload(text: str) -> dict[str, Any]:
    """Extrai o primeiro objeto JSON de uma resposta de modelo."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("resposta LLM vazia")

    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.S | re.I)
    if fence:
        raw = fence.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("JSON raiz nao e objeto")
    return data


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

    def extract_json(
        self,
        *,
        task: str,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
    ) -> StructuredExtractResult:
        return StructuredExtractResult(
            data={},
            provider=self.provider_name,
            used_fallback=True,
            notes=f"task={task}; extract_json indisponivel no provider none",
            raw_text="",
        )


class OllamaLLMClient:
    """Cliente Ollama local (/api/generate) com fallback para template."""

    provider_name = "ollama"

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout_seconds: float = 90.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._fallback = NoneLLMClient()

    def _generate_raw(self, prompt: str, *, temperature: float = 0.1) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        text = str(data.get("response") or "").strip()
        if not text:
            raise RuntimeError("Ollama retornou resposta vazia")
        return text

    def generate(
        self,
        *,
        task: str,
        project_excerpt: str,
        edict_excerpt: str,
        extra: dict[str, Any] | None = None,
    ) -> GenerationResult:
        extra = extra or {}
        prompt = (
            "Voce e um assistente de fomento a inovacao. Redija um rascunho curto de aderencia "
            "projeto-edital em portugues, com secoes claras. Nao invente dados ausentes.\n\n"
            f"Tarefa: {task}\n"
            f"Projeto: {extra.get('project_title') or 'Projeto'}\n"
            f"Empresa: {extra.get('company_name') or 'Empresa'}\n"
            f"Edital: {extra.get('edict_title') or 'Edital'}\n\n"
            f"Trecho do projeto:\n{_clip(project_excerpt, 2500)}\n\n"
            f"Trecho do edital:\n{_clip(edict_excerpt, 2500)}\n"
        )
        try:
            text = self._generate_raw(prompt, temperature=0.2)
            return GenerationResult(
                text=text,
                provider=self.provider_name,
                used_fallback=False,
                notes=f"task={task}; model={self.model}",
            )
        except Exception as exc:  # noqa: BLE001
            result = self._fallback.generate(
                task=task,
                project_excerpt=project_excerpt,
                edict_excerpt=edict_excerpt,
                extra=extra,
            )
            result.provider = self.provider_name
            result.used_fallback = True
            result.notes = f"Ollama falhou ({exc}); usando template"
            return result

    def extract_json(
        self,
        *,
        task: str,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
    ) -> StructuredExtractResult:
        schema_txt = ""
        if schema_hint:
            schema_txt = (
                "\nResponda SOMENTE com um JSON valido (sem markdown) neste formato:\n"
                + json.dumps(schema_hint, ensure_ascii=False, indent=2)
                + "\n"
            )
        full_prompt = (
            "Voce extrai campos de propostas de fomento. Use apenas o texto fornecido. "
            "Se um campo nao existir, use null ou lista vazia. Nao invente.\n"
            f"Tarefa: {task}\n"
            f"{schema_txt}\n"
            f"{prompt}\n"
        )
        try:
            raw = self._generate_raw(full_prompt, temperature=0.0)
            data = parse_json_payload(raw)
            return StructuredExtractResult(
                data=data,
                provider=self.provider_name,
                used_fallback=False,
                notes=f"task={task}; model={self.model}",
                raw_text=raw,
            )
        except Exception as exc:  # noqa: BLE001
            return StructuredExtractResult(
                data={},
                provider=self.provider_name,
                used_fallback=True,
                notes=f"Ollama extract_json falhou ({exc})",
                raw_text="",
            )


class PassthroughFallbackClient:
    """Para provedores futuros (openai/anthropic): se indisponíveis, cai no template."""

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

    def extract_json(
        self,
        *,
        task: str,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
    ) -> StructuredExtractResult:
        return StructuredExtractResult(
            data={},
            provider=self.requested,
            used_fallback=True,
            notes=f"Provedor '{self.requested}' sem extract_json; noop",
            raw_text="",
        )


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    settings = settings or get_settings()
    provider = (settings.llm_provider or "none").strip().lower()
    if provider in {"none", "template", "off", "disabled"}:
        return NoneLLMClient()
    if provider == "ollama":
        return OllamaLLMClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
    return PassthroughFallbackClient(provider)
