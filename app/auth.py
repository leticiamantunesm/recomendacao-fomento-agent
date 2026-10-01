"""Autenticacao Fase A+: senha (PBKDF2) + token HMAC (stdlib)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select

from app.config import get_settings
from db.models import Company, Employee
from db.session import session_scope

_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored or not password:
        return False
    try:
        algo, iters_s, salt, digest = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iters = int(iters_s)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iters,
    ).hex()
    return hmac.compare_digest(check, digest)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    pad = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + pad)


def _sign_payload(payload: dict[str, Any]) -> str:
    settings = get_settings()
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(
        settings.auth_secret.encode("utf-8"),
        body.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{body}.{sig}"


def _decode_signed_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        body, sig = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(401, "Token invalido.") from exc
    expected = hmac.new(
        settings.auth_secret.encode("utf-8"),
        body.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(401, "Token invalido.")
    try:
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(401, "Token invalido.") from exc
    if int(payload.get("exp") or 0) < int(time.time()):
        raise HTTPException(401, "Sessao ou link expirado. Solicite novamente.")
    return payload


def create_access_token(*, employee_id: UUID, company_id: UUID, email: str) -> str:
    settings = get_settings()
    return _sign_payload(
        {
            "eid": str(employee_id),
            "cid": str(company_id),
            "email": email,
            "purpose": "access",
            "exp": int(time.time()) + settings.auth_token_ttl_hours * 3600,
        }
    )


def create_password_reset_token(*, employee_id: UUID, company_id: UUID, email: str) -> str:
    settings = get_settings()
    return _sign_payload(
        {
            "eid": str(employee_id),
            "cid": str(company_id),
            "email": email,
            "purpose": "password_reset",
            "exp": int(time.time()) + settings.auth_reset_ttl_minutes * 60,
        }
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = _decode_signed_token(token)
    if payload.get("purpose") not in {None, "access"}:
        raise HTTPException(401, "Token invalido.")
    return payload


def decode_password_reset_token(token: str) -> dict[str, Any]:
    payload = _decode_signed_token(token)
    if payload.get("purpose") != "password_reset":
        raise HTTPException(400, "Link de redefinicao invalido.")
    return payload


@dataclass
class AuthUser:
    employee_id: UUID
    company_id: UUID
    email: str
    name: str
    role: str
    company_name: str


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Autenticacao necessaria. Faca login.")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(401, "Autenticacao necessaria. Faca login.")
    payload = decode_access_token(token)
    try:
        employee_id = UUID(payload["eid"])
        company_id = UUID(payload["cid"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(401, "Token invalido.") from exc

    async with session_scope() as session:
        emp = await session.get(Employee, employee_id)
        if not emp or not emp.is_active:
            raise HTTPException(401, "Usuario inativo ou nao encontrado.")
        if emp.company_id != company_id:
            raise HTTPException(401, "Token invalido.")
        company = await session.get(Company, company_id)
        if not company:
            raise HTTPException(401, "Empresa nao encontrada.")
        return AuthUser(
            employee_id=emp.id,
            company_id=emp.company_id,
            email=emp.email,
            name=emp.name,
            role=emp.role or "admin",
            company_name=company.name,
        )


async def find_company_by_login_name(session, company_name: str) -> Company | None:
    name = company_name.strip()
    if not name:
        return None
    return await session.scalar(
        select(Company).where((Company.name.ilike(name)) | (Company.trade_name.ilike(name)))
    )
