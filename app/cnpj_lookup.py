"""Lookup publico de CNPJ para preencher cadastro da empresa.

Fontes (nessa ordem):
1. BrasilAPI — https://brasilapi.com.br/api/cnpj/v1/{cnpj}
2. OpenCNPJ — https://api.opencnpj.org/{cnpj}

Em redes corporativas (proxy SSL), se a verificacao de certificado falhar,
a consulta e refeita com verify=False (somente para estas APIs publicas).
"""

from __future__ import annotations

import re
from typing import Any

import httpx

BRASILAPI_CNPJ = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
OPENCNPJ = "https://api.opencnpj.org/{cnpj}"


def normalize_cnpj(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) != 14:
        raise ValueError("CNPJ deve ter 14 digitos")
    return digits


def map_porte(porte: str | None, opcao_mei: str | None = None) -> str | None:
    """Mapeia porte da Receita/BrasilAPI para MEI/ME/EPP/Demais."""
    blob = f"{porte or ''} {opcao_mei or ''}".upper().strip()
    if not blob:
        return None
    if "MEI" in blob or "MICROEMPREENDEDOR" in blob or blob in {"S", "SIM"}:
        # opcao_pelo_mei sozinho nao basta; exige porte MEI no texto
        if "MEI" in blob or "MICROEMPREENDEDOR" in blob:
            return "MEI"
    if re.search(r"\bMEI\b", blob):
        return "MEI"
    if "MICRO EMPRESA" in blob or "MICROEMPRESA" in blob or blob in {"ME", "01", "1"}:
        return "ME"
    if "PEQUENO" in blob or "EPP" in blob or blob in {"EPP", "03", "3"}:
        return "EPP"
    if "DEMAIS" in blob or "GRANDE" in blob or "MEDIO" in blob or "MÉDIO" in blob:
        return "Demais"
    if "MICRO" in blob:
        return "ME"
    return "Demais"


def map_brasilapi_payload(data: dict[str, Any]) -> dict[str, Any]:
    cnae_code = data.get("cnae_fiscal")
    cnae_desc = data.get("cnae_fiscal_descricao")
    cnae = None
    if cnae_code and cnae_desc:
        cnae = f"{cnae_code} - {cnae_desc}"
    elif cnae_desc:
        cnae = str(cnae_desc)
    elif cnae_code:
        cnae = str(cnae_code)

    phone = None
    ddd = data.get("ddd_telefone_1")
    if ddd:
        phone = str(ddd)

    areas: list[str] = []
    if cnae_desc:
        areas.append(str(cnae_desc))
    for sec in data.get("cnaes_secundarios") or []:
        desc = sec.get("descricao") if isinstance(sec, dict) else None
        if desc:
            areas.append(str(desc))

    mei_flag = data.get("opcao_pelo_mei")
    size = map_porte(data.get("porte"), str(mei_flag) if mei_flag is not None else None)
    if str(mei_flag).lower() in {"true", "sim", "s", "1"} and size in {None, "ME"}:
        size = "MEI"

    return {
        "cnpj": data.get("cnpj"),
        "name": data.get("razao_social") or data.get("nome_fantasia"),
        "trade_name": data.get("nome_fantasia"),
        "size": size,
        "porte_raw": data.get("porte"),
        "uf": data.get("uf"),
        "city": data.get("municipio"),
        "cnae": cnae,
        "email": data.get("email"),
        "phone": phone,
        "areas": areas[:8],
        "capital_social": data.get("capital_social"),
        "situacao_cadastral": data.get("descricao_situacao_cadastral"),
        "source": "brasilapi",
    }


def map_opencnpj_payload(data: dict[str, Any]) -> dict[str, Any]:
    # OpenCNPJ schema varia; campos comuns:
    razao = data.get("razao_social") or data.get("nome") or data.get("company", {}).get("name")
    fantasia = data.get("nome_fantasia") or data.get("fantasia")
    porte = data.get("porte") or data.get("company_size")
    endereco = data.get("endereco") or {}
    if isinstance(endereco, dict):
        uf = endereco.get("uf") or data.get("uf")
        city = endereco.get("municipio") or endereco.get("cidade") or data.get("municipio")
    else:
        uf = data.get("uf")
        city = data.get("municipio")
    cnae = data.get("cnae_principal") or data.get("cnae")
    if isinstance(cnae, dict):
        cnae = f"{cnae.get('codigo') or ''} - {cnae.get('descricao') or ''}".strip(" -")
    return {
        "cnpj": data.get("cnpj") or data.get("tax_id"),
        "name": razao or fantasia,
        "trade_name": fantasia,
        "size": map_porte(str(porte) if porte else None),
        "porte_raw": porte,
        "uf": uf,
        "city": city,
        "cnae": str(cnae) if cnae else None,
        "email": data.get("email"),
        "phone": data.get("telefone") or data.get("phone"),
        "areas": [str(cnae)] if cnae else [],
        "capital_social": data.get("capital_social"),
        "situacao_cadastral": data.get("situacao") or data.get("situacao_cadastral"),
        "source": "opencnpj",
    }


async def _get_json(url: str) -> dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": "recomendacao-fomento-agent/0.3"}
    last_err: Exception | None = None
    for verify in (True, False):
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=verify) as client:
                resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                raise LookupError("CNPJ nao encontrado na base publica")
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code} em {url}")
            data = resp.json()
            if not isinstance(data, dict):
                raise RuntimeError("Resposta inesperada da API de CNPJ")
            return data
        except LookupError:
            raise
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    raise RuntimeError(f"Falha ao consultar CNPJ: {last_err}")


async def lookup_cnpj(cnpj_raw: str) -> dict[str, Any]:
    cnpj = normalize_cnpj(cnpj_raw)
    errors: list[str] = []

    try:
        data = await _get_json(BRASILAPI_CNPJ.format(cnpj=cnpj))
        mapped = map_brasilapi_payload(data)
        mapped["cnpj"] = cnpj
        if mapped.get("name"):
            return mapped
        errors.append("BrasilAPI sem razao social")
    except LookupError:
        raise
    except Exception as exc:  # noqa: BLE001
        errors.append(f"BrasilAPI: {exc}")

    try:
        data = await _get_json(OPENCNPJ.format(cnpj=cnpj))
        mapped = map_opencnpj_payload(data)
        mapped["cnpj"] = cnpj
        if mapped.get("name"):
            return mapped
        errors.append("OpenCNPJ sem razao social")
    except LookupError:
        raise
    except Exception as exc:  # noqa: BLE001
        errors.append(f"OpenCNPJ: {exc}")

    raise RuntimeError(" | ".join(errors) or "Falha desconhecida na consulta de CNPJ")
