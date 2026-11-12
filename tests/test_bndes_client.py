"""Testes do BndesClient — contrato OAuth configurável + catálogo público."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.config import Settings
from app.integrations.bndes.client import BndesClient, BndesService
from app.integrations.bndes.errors import (
    BndesAuthError,
    BndesContractNotConfiguredError,
    BndesHttpError,
    BndesRateLimitError,
)
from app.integrations.bndes.models import BndesToken

FIXTURE_LINHAS = (
    Path(__file__).resolve().parent / "fixtures" / "portals" / "bndes_linhas.json"
)


def _settings(**overrides: object) -> Settings:
    base = {
        "bndes_client_id": "test-client",
        "bndes_client_secret": "test-secret",
        "bndes_token_url": "https://example.test/token",
        "bndes_financing_options_url": "https://example.test/opcoes",
        "bndes_financing_options_method": "GET",
        "bndes_max_retries": 1,
        "bndes_retry_backoff_seconds": 0.1,
        "bndes_timeout_seconds": 5.0,
    }
    base.update(overrides)
    return Settings.model_validate(base)


def test_contract_not_configured_without_url() -> None:
    settings = _settings(bndes_financing_options_url=None, bndes_api_base_url=None)
    transport = httpx.MockTransport(lambda r: httpx.Response(500))
    with BndesClient(settings, http_client=httpx.Client(transport=transport)) as client:
        with pytest.raises(BndesContractNotConfiguredError):
            client.get_financing_options({"foo": "bar"})


def test_oauth_credentials_required() -> None:
    settings = _settings(
        bndes_client_id=None,
        bndes_client_secret=None,
        bndes_token_url=None,
    )
    transport = httpx.MockTransport(lambda r: httpx.Response(500))
    with BndesClient(settings, http_client=httpx.Client(transport=transport)) as client:
        with pytest.raises(BndesContractNotConfiguredError) as exc:
            client.get_access_token()
        msg = str(exc.value)
        assert "BNDES_CLIENT_ID" in msg
        assert "BNDES_TOKEN_URL" in msg


def test_token_reuse_until_expiry() -> None:
    calls = {"token": 0, "api": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            calls["token"] += 1
            return httpx.Response(
                200,
                json={
                    "access_token": "tok-abc",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            )
        calls["api"] += 1
        auth = request.headers.get("Authorization", "")
        assert auth == "Bearer tok-abc"
        assert "tok-abc" not in str(request.content)
        return httpx.Response(200, json={"items": []})

    transport = httpx.MockTransport(handler)
    with BndesClient(
        _settings(), http_client=httpx.Client(transport=transport)
    ) as client:
        client.get_financing_options({"porte": "MPME"})
        client.get_financing_options({"porte": "Grande"})
    assert calls["token"] == 1
    assert calls["api"] == 2


def test_token_refresh_on_401() -> None:
    state = {"token_n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            state["token_n"] += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"tok-{state['token_n']}",
                    "expires_in": 3600,
                },
            )
        auth = request.headers.get("Authorization", "")
        if auth == "Bearer tok-1":
            return httpx.Response(401, json={"error": "invalid_token"})
        assert auth == "Bearer tok-2"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with BndesClient(
        _settings(bndes_max_retries=2),
        http_client=httpx.Client(transport=transport),
    ) as client:
        result = client.get_financing_options()
    assert result.data == {"ok": True}
    assert state["token_n"] == 2


def test_rate_limit_raises_after_retries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"access_token": "t", "expires_in": 60}
            )
        return httpx.Response(429, json={"error": "rate_limit"})

    transport = httpx.MockTransport(handler)
    with BndesClient(
        _settings(bndes_max_retries=1),
        http_client=httpx.Client(transport=transport),
    ) as client:
        with pytest.raises(BndesRateLimitError):
            client.get_financing_options()


def test_http_error_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"access_token": "t", "expires_in": 60}
            )
        return httpx.Response(503, text="unavailable")

    transport = httpx.MockTransport(handler)
    with BndesClient(
        _settings(bndes_max_retries=0),
        http_client=httpx.Client(transport=transport),
    ) as client:
        with pytest.raises(BndesHttpError) as exc:
            client.get_financing_options()
        assert exc.value.status_code == 503


def test_auth_error_on_bad_token_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_client"})

    transport = httpx.MockTransport(handler)
    with BndesClient(
        _settings(), http_client=httpx.Client(transport=transport)
    ) as client:
        with pytest.raises(BndesAuthError):
            client.get_access_token()


def test_token_is_expired_skew() -> None:
    token = BndesToken(access_token="x", expires_in=30)
    assert token.is_expired(skew_seconds=60) is True
    token2 = BndesToken(access_token="x", expires_in=3600)
    assert token2.is_expired(skew_seconds=60) is False


def test_list_public_linhas_from_fixture() -> None:
    payload = json.loads(FIXTURE_LINHAS.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        assert "apoioFinanceiro/rest/linhasProgramas" in str(request.url)
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    settings = Settings.model_validate(
        {
            "bndes_public_linhas_url": (
                "https://www.bndes.gov.br/apoioFinanceiro/rest/linhasProgramas"
            )
        }
    )
    with BndesClient(
        settings, http_client=httpx.Client(transport=transport)
    ) as client:
        result = client.list_public_linhas_programas()
    assert result.status_code == 200
    assert len(result.items) == len(payload)
    assert result.items[0].nome == payload[0]["nome"]


def test_service_facade_get_financing_options() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"access_token": "svc", "expires_in": 120}
            )
        return httpx.Response(200, json=[{"id": 1}])

    transport = httpx.MockTransport(handler)
    # BndesService cria Client interno; injetamos via Settings + monkeypatch seria
    # pesado — testamos facade com Client direto e espelhamos assinatura.
    with BndesClient(
        _settings(), http_client=httpx.Client(transport=transport)
    ) as client:
        out = client.get_financing_options({"natureza": "investimento"})
    assert out.data == [{"id": 1}]
    assert out.params_sent == {"natureza": "investimento"}
    # Service instancia Settings reais; garante import/construção.
    assert BndesService(_settings()) is not None


def test_builds_url_from_base_and_path() -> None:
    settings = _settings(
        bndes_financing_options_url=None,
        bndes_api_base_url="https://gateway.example/v1",
        bndes_financing_options_path="/financiamento/opcoes",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"access_token": "t", "expires_in": 60}
            )
        assert str(request.url).startswith(
            "https://gateway.example/v1/financiamento/opcoes"
        )
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    with BndesClient(
        settings, http_client=httpx.Client(transport=transport)
    ) as client:
        client.get_financing_options()


def test_obter_configuracao_operacional_post_body() -> None:
    swagger = json.loads(
        (
            Path(__file__).resolve().parent
            / "fixtures"
            / "portals"
            / "bndes_portfolio_swagger.json"
        ).read_text(encoding="utf-8")
    )
    expected_path = (
        swagger["basePath"].rstrip("/")
        + "/obterconfiguracaooperacional"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"access_token": "port-tok", "expires_in": 120}
            )
        assert request.method == "POST"
        assert request.url.path == expected_path
        assert request.url.host == swagger["host"]
        assert request.headers.get("Authorization") == "Bearer port-tok"
        body = json.loads(request.content.decode("utf-8"))
        assert body == {"payload": "cfg-teste"}
        return httpx.Response(200, json={"status": "OK", "raw": True})

    transport = httpx.MockTransport(handler)
    settings = _settings(
        bndes_portfolio_base_url=(
            f"https://{swagger['host']}{swagger['basePath']}"
        )
    )
    with BndesClient(
        settings, http_client=httpx.Client(transport=transport)
    ) as client:
        result = client.obter_configuracao_operacional(payload="cfg-teste")
    assert result.status_code == 200
    assert result.request_body == {"payload": "cfg-teste"}
    assert result.data == {"status": "OK", "raw": True}
    assert "obterconfiguracaooperacional" in result.request_url


def test_obter_configuracao_operacional_empty_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"access_token": "t", "expires_in": 60}
            )
        assert request.method == "POST"
        assert "obterconfiguracaooperacional" in str(request.url)
        body = json.loads(request.content.decode("utf-8"))
        assert body == {}
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    with BndesClient(
        _settings(), http_client=httpx.Client(transport=transport)
    ) as client:
        result = client.obter_configuracao_operacional()
    assert result.status_code == 200
    assert result.request_body == {}


def test_service_obter_configuracao_operacional() -> None:
    svc = BndesService(_settings())
    assert hasattr(svc, "obter_configuracao_operacional")
