"""Cliente server-side BNDES (OAuth Developers@BNDES + catálogo público).

Não inventa path/params da API \"Opções de financiamento\": exige URL configurada
a partir do Swagger oficial da Loja (ver docs/integrations/BNDES_API_OPCOES_FINANCIAMENTO.md).
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any, Mapping
from urllib.parse import urljoin

import httpx

from app.config import Settings, get_settings
from app.integrations.bndes.errors import (
    BndesAuthError,
    BndesContractNotConfiguredError,
    BndesHttpError,
    BndesRateLimitError,
    BndesTimeoutError,
)
from app.integrations.bndes.models import (
    BndesFinancingOptionsResult,
    BndesPortfolioConfigResult,
    BndesPublicLinhaPrograma,
    BndesPublicLinhasResult,
    BndesToken,
)

logger = logging.getLogger(__name__)

# Endpoint público real do Navegador de Financiamentos (já usado em agents/sources/bndes.py).
DEFAULT_PUBLIC_LINHAS_URL = (
    "https://www.bndes.gov.br/apoioFinanceiro/rest/linhasProgramas"
)

# Contrato Swagger Portfólio v1 (host homolog + basePath + path).
DEFAULT_PORTFOLIO_BASE_URL = "https://gateway-h.apis.bndes.gov.br/produtos/v1"
PORTFOLIO_OBTER_CONFIG_PATH = "/obterconfiguracaooperacional"


class BndesClient:
    """Integração HTTP com APIs BNDES (credenciais só no servidor)."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._owns_client = http_client is None
        timeout = float(getattr(self._settings, "bndes_timeout_seconds", 30.0) or 30.0)
        verify = bool(getattr(self._settings, "bndes_verify_ssl", True))
        self._client = http_client or httpx.Client(timeout=timeout, verify=verify)
        self._token: BndesToken | None = None
        self._max_retries = int(getattr(self._settings, "bndes_max_retries", 2) or 0)
        self._retry_backoff = float(
            getattr(self._settings, "bndes_retry_backoff_seconds", 1.0) or 1.0
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> BndesClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ------------------------------------------------------------------ auth
    def _require_oauth_credentials(self) -> tuple[str, str, str]:
        client_id = (self._settings.bndes_client_id or "").strip()
        client_secret = (self._settings.bndes_client_secret or "").strip()
        token_url = (self._settings.bndes_token_url or "").strip()
        missing: list[str] = []
        if not client_id:
            missing.append("BNDES_CLIENT_ID")
        if not client_secret:
            missing.append("BNDES_CLIENT_SECRET")
        if not token_url:
            missing.append("BNDES_TOKEN_URL")
        if missing:
            raise BndesContractNotConfiguredError(
                "Autenticação BNDES incompleta. Defina: "
                + ", ".join(missing)
                + ". Obtenha client_id/secret na Loja de APIs e a token URL "
                "no Swagger/Console da API \"Opções de financiamento\" "
                "(docs/integrations/BNDES_API_OPCOES_FINANCIAMENTO.md)."
            )
        return client_id, client_secret, token_url

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        """Obtém/reutiliza access token OAuth2 client_credentials (não loga o token)."""
        if (
            not force_refresh
            and self._token is not None
            and not self._token.is_expired()
        ):
            return self._token.access_token

        client_id, client_secret, token_url = self._require_oauth_credentials()
        scope = (self._settings.bndes_oauth_scope or "").strip() or None

        basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode(
            "ascii"
        )
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data: dict[str, str] = {"grant_type": "client_credentials"}
        if scope:
            data["scope"] = scope

        logger.info(
            "bndes_oauth_token_request",
            extra={
                "token_host": httpx.URL(token_url).host,
                "has_scope": bool(scope),
                "force_refresh": force_refresh,
            },
        )

        try:
            response = self._client.post(token_url, headers=headers, data=data)
        except httpx.TimeoutException as exc:
            raise BndesTimeoutError("Timeout ao solicitar token BNDES") from exc
        except httpx.HTTPError as exc:
            raise BndesAuthError(f"Falha de rede ao solicitar token BNDES: {exc}") from exc

        if response.status_code >= 400:
            logger.warning(
                "bndes_oauth_token_http_error status=%s",
                response.status_code,
            )
            raise BndesAuthError(
                f"Token BNDES recusado (HTTP {response.status_code})",
                status_code=response.status_code,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise BndesAuthError("Resposta de token BNDES não é JSON") from exc

        access = payload.get("access_token")
        if not access or not isinstance(access, str):
            raise BndesAuthError("Resposta de token BNDES sem access_token")

        expires_in = payload.get("expires_in")
        try:
            expires_int = int(expires_in) if expires_in is not None else None
        except (TypeError, ValueError):
            expires_int = None

        self._token = BndesToken(
            access_token=access,
            token_type=str(payload.get("token_type") or "Bearer"),
            expires_in=expires_int,
            scope=payload.get("scope") if isinstance(payload.get("scope"), str) else scope,
        )
        logger.info(
            "bndes_oauth_token_ok expires_in=%s",
            expires_int,
        )
        return self._token.access_token

    def invalidate_token(self) -> None:
        self._token = None

    # ------------------------------------------------ authenticated HTTP
    def _sleep_backoff(self, attempt: int) -> None:
        delay = self._retry_backoff * (2**attempt)
        time.sleep(delay)

    def _request_authenticated_json(
        self,
        *,
        method: str,
        url: str,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        operation: str,
    ) -> tuple[httpx.Response, Any]:
        """GET/POST autenticado com retry (timeout, 429, 401→refresh)."""
        query = {k: v for k, v in dict(query or {}).items() if v is not None}
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                token = self.get_access_token()
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                }
                if body is not None:
                    headers["Content-Type"] = "application/json"

                logger.info(
                    "bndes_api_request op=%s method=%s attempt=%s params_keys=%s has_body=%s",
                    operation,
                    method,
                    attempt,
                    sorted(query.keys()),
                    body is not None,
                )
                try:
                    response = self._client.request(
                        method,
                        url,
                        params=query or None,
                        json=body,
                        headers=headers,
                    )
                except httpx.TimeoutException as exc:
                    raise BndesTimeoutError(
                        f"Timeout BNDES em {operation}"
                    ) from exc
                except httpx.HTTPError as exc:
                    raise BndesHttpError(
                        f"Falha de rede BNDES em {operation}: {exc}"
                    ) from exc

                if response.status_code == 401:
                    self.invalidate_token()
                    raise BndesAuthError(
                        f"API BNDES rejeitou o access token em {operation} (HTTP 401)",
                        status_code=401,
                    )
                if response.status_code == 429:
                    raise BndesRateLimitError(
                        f"Rate limit BNDES em {operation} (HTTP 429)",
                        status_code=429,
                    )
                if response.status_code >= 400:
                    logger.warning(
                        "bndes_api_http_error op=%s status=%s",
                        operation,
                        response.status_code,
                    )
                    raise BndesHttpError(
                        f"BNDES {operation} HTTP {response.status_code}",
                        status_code=response.status_code,
                    )

                if not response.content:
                    return response, None
                try:
                    return response, response.json()
                except ValueError as exc:
                    raise BndesHttpError(
                        f"Resposta BNDES {operation} não é JSON",
                        status_code=response.status_code,
                    ) from exc

            except BndesRateLimitError as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise
                self._sleep_backoff(attempt)
            except BndesTimeoutError as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise
                self._sleep_backoff(attempt)
            except BndesAuthError as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise
                logger.info("bndes_auth_retry_after_401_or_auth_error op=%s", operation)
                self.invalidate_token()
                self._sleep_backoff(attempt)

        assert last_error is not None
        raise last_error

    # ------------------------------------------------ Portfólio (Swagger v1)
    def _portfolio_obter_config_url(self) -> str:
        explicit = (self._settings.bndes_portfolio_obter_config_url or "").strip()
        if explicit:
            return explicit
        base = (
            (self._settings.bndes_portfolio_base_url or "").strip()
            or DEFAULT_PORTFOLIO_BASE_URL
        )
        return urljoin(base.rstrip("/") + "/", PORTFOLIO_OBTER_CONFIG_PATH.lstrip("/"))

    def obter_configuracao_operacional(
        self,
        payload: str | None = None,
    ) -> BndesPortfolioConfigResult:
        """POST /produtos/v1/obterconfiguracaooperacional (API Portfólio).

        Contrato Swagger 2.0:
        - body opcional ``{\"payload\": \"<string>\"}``
        - response 200 sem schema de campos (retornamos ``data`` opaco)
        """
        url = self._portfolio_obter_config_url()
        body: dict[str, Any] = {}
        if payload is not None:
            body["payload"] = payload

        response, data = self._request_authenticated_json(
            method="POST",
            url=url,
            body=body,
            operation="portfolio_obterconfiguracaooperacional",
        )
        return BndesPortfolioConfigResult(
            request_url=str(response.url),
            status_code=response.status_code,
            request_body=body,
            data=data,
        )

    # ------------------------------------------------ financing options OAuth
    def _financing_options_url(self) -> str:
        """Monta URL apenas a partir de env (sem path inventado no código)."""
        explicit = (self._settings.bndes_financing_options_url or "").strip()
        if explicit:
            return explicit

        base = (self._settings.bndes_api_base_url or "").strip()
        path = (self._settings.bndes_financing_options_path or "").strip()
        if base and path:
            return urljoin(base.rstrip("/") + "/", path.lstrip("/"))

        raise BndesContractNotConfiguredError(
            "URL da API \"Opções de financiamento\" não configurada. "
            "Preencha BNDES_FINANCING_OPTIONS_URL (preferencial) ou "
            "BNDES_API_BASE_URL + BNDES_FINANCING_OPTIONS_PATH com valores "
            "copiados do Swagger oficial na Loja Developers@BNDES. "
            "Ver docs/integrations/BNDES_API_OPCOES_FINANCIAMENTO.md. "
            "Para a API Portfólio use obter_configuracao_operacional()."
        )

    def get_financing_options(
        self,
        params: Mapping[str, Any] | None = None,
        *,
        method: str | None = None,
        json_body: Mapping[str, Any] | None = None,
    ) -> BndesFinancingOptionsResult:
        """Consulta opções de financiamento na API OAuth oficial (se URL configurada).

        Aceita apenas o que o operador configurar:
        - ``params``: query string (nomes reais do Swagger — não inventados aqui)
        - ``method``: sobrescreve BNDES_FINANCING_OPTIONS_METHOD (default GET)
        - ``json_body``: body se o contrato oficial for POST/PUT

        Sem URL de contrato configurada, levanta ``BndesContractNotConfiguredError``.
        """
        url = self._financing_options_url()
        http_method = (
            method
            or (self._settings.bndes_financing_options_method or "GET")
        ).strip().upper()
        if http_method not in {"GET", "POST", "PUT", "PATCH"}:
            raise BndesContractNotConfiguredError(
                f"Método HTTP inválido para Opções de financiamento: {http_method!r}"
            )

        query = {k: v for k, v in dict(params or {}).items() if v is not None}
        body = dict(json_body) if json_body is not None else None

        response, data = self._request_authenticated_json(
            method=http_method,
            url=url,
            query=query,
            body=body,
            operation="opcoes_financiamento",
        )
        return BndesFinancingOptionsResult(
            request_url=str(response.url),
            status_code=response.status_code,
            params_sent=query,
            data=data,
        )

    # ------------------------------------------------ public navegador catalog
    def list_public_linhas_programas(
        self,
        *,
        url: str | None = None,
    ) -> BndesPublicLinhasResult:
        """GET público do Navegador (não é a API OAuth Developers@BNDES)."""
        target = (url or self._settings.bndes_public_linhas_url or "").strip()
        if not target:
            target = DEFAULT_PUBLIC_LINHAS_URL

        logger.info("bndes_public_linhas_request")
        try:
            response = self._client.get(
                target,
                headers={"Accept": "application/json"},
            )
        except httpx.TimeoutException as exc:
            raise BndesTimeoutError("Timeout ao listar linhas públicas BNDES") from exc
        except httpx.HTTPError as exc:
            raise BndesHttpError(f"Falha de rede linhas públicas BNDES: {exc}") from exc

        if response.status_code == 429:
            raise BndesRateLimitError(
                "Rate limit linhas públicas BNDES (HTTP 429)",
                status_code=429,
            )
        if response.status_code >= 400:
            raise BndesHttpError(
                f"Linhas públicas BNDES HTTP {response.status_code}",
                status_code=response.status_code,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise BndesHttpError(
                "Resposta linhas públicas BNDES não é JSON",
                status_code=response.status_code,
            ) from exc

        if not isinstance(payload, list):
            raise BndesHttpError(
                "Resposta linhas públicas BNDES não é uma lista JSON",
                status_code=response.status_code,
            )

        items = [
            BndesPublicLinhaPrograma.model_validate(row)
            for row in payload
            if isinstance(row, dict)
        ]
        return BndesPublicLinhasResult(
            request_url=str(response.url),
            status_code=response.status_code,
            items=items,
        )


class BndesService:
    """Fachada de serviço alinhada ao restante do SADS (usa Settings)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def obter_configuracao_operacional(
        self,
        payload: str | None = None,
    ) -> BndesPortfolioConfigResult:
        with BndesClient(self._settings) as client:
            return client.obter_configuracao_operacional(payload)

    def get_financing_options(
        self,
        params: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> BndesFinancingOptionsResult:
        with BndesClient(self._settings) as client:
            return client.get_financing_options(params, **kwargs)

    def list_public_linhas_programas(self) -> BndesPublicLinhasResult:
        with BndesClient(self._settings) as client:
            return client.list_public_linhas_programas()
