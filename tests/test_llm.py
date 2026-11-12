"""Testes do LLM none + template (T-006) e factory Ollama."""

from app.llm import NoneLLMClient, OllamaLLMClient, get_llm_client, render_template_draft
from app.config import Settings
from agents.generation_agent import DraftRequest, GenerationAgent


def test_template_contains_sections() -> None:
    text = render_template_draft(
        project_excerpt="Projeto de inovação em sensores.",
        edict_excerpt="Edital FINEP para tecnologias digitais.",
        extra={"project_title": "Sensores", "edict_title": "FINEP Dig"},
    )
    assert "Resumo do projeto" in text
    assert "Sensores" in text
    assert "FINEP Dig" in text


def test_none_client_uses_fallback() -> None:
    client = NoneLLMClient()
    result = client.generate(
        task="draft",
        project_excerpt="abc",
        edict_excerpt="xyz",
    )
    assert result.provider == "none"
    assert result.used_fallback is True
    assert "Rascunho" in result.text


def test_get_llm_client_none() -> None:
    settings = Settings(LLM_PROVIDER="none")
    client = get_llm_client(settings)
    assert isinstance(client, NoneLLMClient)


def test_get_llm_client_ollama() -> None:
    settings = Settings(
        LLM_PROVIDER="ollama",
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="llama3.2",
        DATABASE_URL="postgresql://u:p@localhost/db",
    )
    client = get_llm_client(settings)
    assert isinstance(client, OllamaLLMClient)
    assert client.model == "llama3.2"


def test_generation_agent_smoke() -> None:
    agent = GenerationAgent()
    result = agent.draft(
        DraftRequest(
            project_title="Demo",
            project_text="Texto do projeto " * 30,
            edict_title="Edital Demo",
            edict_text="Texto do edital " * 30,
            company_name="Empresa Demo TCC",
        )
    )
    assert result.used_fallback is True
    assert "Empresa Demo TCC" in result.text
