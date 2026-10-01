"""Configuração central do projeto (pydantic-settings) — T-003 / RT-28."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent

_ALLOWED_LLM = {"none", "template", "off", "disabled", "ollama", "openai", "anthropic"}


class Settings(BaseSettings):
    """Variáveis de ambiente carregadas de `.env` na raiz do repositório."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql://neondb_owner:SUA_SENHA@ep-XXXX.sa-east-1.aws.neon.tech/neondb?sslmode=require",
        alias="DATABASE_URL",
        description="Connection string Neon (ou Postgres local).",
    )

    llm_provider: str = Field(
        default="none",
        alias="LLM_PROVIDER",
        description="Provedor LLM do MVP: none (template, custo zero).",
    )
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )
    data_dir: Path = Field(default=ROOT_DIR / "data", alias="DATA_DIR")
    raw_pdfs_dir: Path = Field(default=ROOT_DIR / "data" / "raw_pdfs", alias="RAW_PDFS_DIR")
    texts_dir: Path = Field(default=ROOT_DIR / "data" / "texts", alias="TEXTS_DIR")
    outputs_dir: Path = Field(default=ROOT_DIR / "data" / "outputs", alias="OUTPUTS_DIR")

    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL_NAME",
    )
    embedding_backend: str = Field(
        default="auto",
        alias="EMBEDDING_BACKEND",
        description="auto | sentence-transformers | hashing (offline)",
    )

    app_name: str = "recomendacao-fomento-agent"
    app_env: str = Field(default="development", alias="APP_ENV")
    auth_secret: str = Field(
        default="sads-dev-change-me-in-production",
        alias="AUTH_SECRET",
        description="Segredo para assinar tokens de sessao (trocar em producao).",
    )
    auth_token_ttl_hours: int = Field(
        default=72,
        alias="AUTH_TOKEN_TTL_HOURS",
        ge=1,
        le=24 * 30,
    )
    auth_reset_ttl_minutes: int = Field(
        default=60,
        alias="AUTH_RESET_TTL_MINUTES",
        ge=5,
        le=24 * 60,
    )
    app_public_url: str = Field(
        default="http://127.0.0.1:8000",
        alias="APP_PUBLIC_URL",
        description="URL publica do app (usada nos links de e-mail).",
    )
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    @field_validator("data_dir", "raw_pdfs_dir", "texts_dir", "outputs_dir", mode="before")
    @classmethod
    def _resolve_path(cls, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path

    @field_validator("llm_provider", mode="before")
    @classmethod
    def _normalize_llm_provider(cls, value: str | None) -> str:
        provider = (value or "none").strip().lower()
        if provider not in _ALLOWED_LLM:
            return "none"
        return provider

    @property
    def llm_uses_template_fallback(self) -> bool:
        return self.llm_provider in {"none", "template", "off", "disabled"}

    @property
    def async_database_url(self) -> str:
        """URL compatível com SQLAlchemy async + asyncpg."""
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url[len("postgresql://") :]
        return url

    @property
    def database_host_hint(self) -> str:
        """Host mascarado para logs/health (sem senha)."""
        try:
            after_at = self.database_url.split("@", 1)[1]
            host = after_at.split("/", 1)[0]
            return host.split("?")[0]
        except IndexError:
            return "(invalid-DATABASE_URL)"


@lru_cache
def get_settings() -> Settings:
    return Settings()
