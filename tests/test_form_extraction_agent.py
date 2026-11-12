"""Testes do FormExtractionAgent (heuristica + merge Ollama mock)."""

from __future__ import annotations

from typing import Any

from agents.form_extraction_agent import FormExtractionAgent, _merge_llm_into_form
from app.config import Settings
from app.llm import StructuredExtractResult, parse_json_payload
from app.pdf_form import guess_form_fields


class _FakeOllama:
    provider_name = "ollama"

    def __init__(self, data: dict[str, Any], *, used_fallback: bool = False) -> None:
        self.data = data
        self.used_fallback = used_fallback

    def generate(self, **kwargs: Any) -> Any:  # noqa: ANN401
        raise NotImplementedError

    def extract_json(
        self,
        *,
        task: str,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
    ) -> StructuredExtractResult:
        return StructuredExtractResult(
            data=self.data,
            provider="ollama",
            used_fallback=self.used_fallback,
            notes=f"fake task={task}",
            raw_text="{}",
        )


def test_parse_json_payload_fence() -> None:
    raw = 'Aqui vai:\n```json\n{"summary": "ok", "objectives": ["a"]}\n```\n'
    data = parse_json_payload(raw)
    assert data["summary"] == "ok"
    assert data["objectives"] == ["a"]


def test_merge_llm_fills_weak_fields() -> None:
    form = guess_form_fields("texto curto demais")
    # forca campo fraco
    form["methodology"] = ""
    form["confidence"]["methodology"] = 0.1
    filled = _merge_llm_into_form(
        form,
        {
            "methodology": "Co-design, prototipagem e validacao em campo com cooperativas.",
            "areas": ["agro", "visão computacional"],
        },
        ["methodology", "areas"],
    )
    assert "methodology" in filled
    assert "co-design" in form["methodology"].lower()
    assert "agro" in form["areas"]


def test_agent_uses_ollama_when_configured() -> None:
    settings = Settings(
        LLM_PROVIDER="ollama",
        FORM_EXTRACT_USE_LLM=True,
        DATABASE_URL="postgresql://u:p@localhost/db",
    )
    fake = _FakeOllama(
        {
            "team": "Coordenador tecnico Dr. Lucas; CEO Mariana Alves Ribeiro.",
            "counterpart": "Contrapartida financeira e economica de R$ 240.000 cada.",
        }
    )
    text = """
    SEMENTE VIVA — Plataforma de Visao Computacional
    1. Resumo
    Projeto de classificacao de sementes para agricultura familiar com estacao portatil.
    6. Objetivos
    Objetivo geral: desenvolver plataforma portatil ate TRL 7 com acuracia macro alta.
    7. Metodologia
    Ciclos de co-design e validacao experimental com dataset anotado.
    Duracao: 24 meses. Valor total R$ 2.400.000
    """
    agent = FormExtractionAgent(settings=settings, llm=fake)  # type: ignore[arg-type]
    result = agent.extract(text, filename="semente.pdf")
    assert result.method == "heuristic+ollama"
    assert result.filled_by_llm
    assert "240.000" in (result.form.get("counterpart") or "")


def test_agent_skips_llm_when_provider_none() -> None:
    settings = Settings(
        LLM_PROVIDER="none",
        FORM_EXTRACT_USE_LLM=True,
        DATABASE_URL="postgresql://u:p@localhost/db",
    )
    fake = _FakeOllama({"summary": "nao deve aplicar"})
    agent = FormExtractionAgent(settings=settings, llm=fake)  # type: ignore[arg-type]
    result = agent.extract(
        "Projeto demo com inovacao agro e metodologia experimental detalhada em campo.",
        filename="x.pdf",
    )
    assert result.method == "heuristic"
    assert result.filled_by_llm == []
