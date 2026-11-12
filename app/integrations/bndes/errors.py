"""Erros normalizados da integração BNDES (sem credenciais na mensagem)."""

from __future__ import annotations


class BndesApiError(Exception):
    """Erro base da integração BNDES."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class BndesContractNotConfiguredError(BndesApiError):
    """Contrato oficial incompleto: URL/path/token não preenchidos via env."""


class BndesAuthError(BndesApiError):
    """Falha ao obter ou renovar access token."""


class BndesHttpError(BndesApiError):
    """Resposta HTTP de erro da API (exceto rate limit)."""


class BndesRateLimitError(BndesHttpError):
    """HTTP 429 ou equivalente de rate limit."""


class BndesTimeoutError(BndesApiError):
    """Timeout de rede / leitura."""
