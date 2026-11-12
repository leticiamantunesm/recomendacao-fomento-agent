"""Tipos tipados da integração BNDES.

O schema da API OAuth \"Opções de financiamento\" ainda não está público
sem login na Loja. Até o Swagger oficial ser preenchido no .env / documentação,
a resposta OAuth é encapsulada de forma opaca (raw) para não inventar campos.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BndesToken(BaseModel):
    """Access token OAuth2 em memória (nunca logar)."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    scope: str | None = None
    obtained_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def is_expired(self, *, skew_seconds: int = 60) -> bool:
        if self.expires_in is None:
            return False
        obtained = self.obtained_at
        if obtained.tzinfo is None:
            obtained = obtained.replace(tzinfo=UTC)
        age = (datetime.now(UTC) - obtained).total_seconds()
        return age >= max(0, self.expires_in - skew_seconds)


class BndesFinancingOptionsResult(BaseModel):
    """Resultado tipado da consulta OAuth (payload bruto até schema oficial)."""

    model_config = ConfigDict(extra="forbid")

    source: str = "developers_bndes_opcoes_financiamento"
    request_url: str
    status_code: int
    params_sent: dict[str, Any] = Field(default_factory=dict)
    data: Any
    # Quando o contrato OpenAPI for anexado, campos tipados podem ser
    # derivados de `data` sem mudar a assinatura pública do client.


class BndesPortfolioConfigRequest(BaseModel):
    """Body oficial POST /obterconfiguracaooperacional (Swagger Portfólio v1)."""

    model_config = ConfigDict(extra="forbid")

    payload: str | None = None


class BndesPortfolioConfigResult(BaseModel):
    """Resposta tipada; schema de negócio do 200 não veio no Swagger (só 'OK')."""

    model_config = ConfigDict(extra="forbid")

    source: str = "developers_bndes_portfolio_obterconfiguracaooperacional"
    request_url: str
    status_code: int
    request_body: dict[str, Any] = Field(default_factory=dict)
    data: Any


class BndesPublicLinhaPrograma(BaseModel):
    """Item do catálogo público GET /apoioFinanceiro/rest/linhasProgramas."""

    model_config = ConfigDict(extra="allow")

    nome: str | None = None
    titulo: str | None = None
    infoBasicas: str | None = None
    setores: list[Any] | None = None
    finalidades: list[Any] | None = None
    qualificadores: list[Any] | None = None
    mpme: bool | None = None
    aviso: str | None = None
    url: str | None = None
    expirado: bool | None = None


class BndesPublicLinhasResult(BaseModel):
    source: str = "bndes_navegador_linhas_programas"
    request_url: str
    status_code: int
    items: list[BndesPublicLinhaPrograma]
