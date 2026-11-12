"""Criptografia at-rest de dossiês (stdlib: HMAC-SHA256 CTR + tag).

Formato binário (arquivos): ``SADS1`` + nonce(16) + ciphertext + tag(32)
Formato texto/JSON: ``sads1:`` + base64url(nonce + ciphertext + tag)

Sem ``PROJECT_DATA_ENCRYPTION_KEY``, as funções são pass-through (legado em claro).
A chave NUNCA deve ir ao frontend. O servidor decifra em memória para analisar
(não é criptografia ponta a ponta).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

_FILE_MAGIC = b"SADS1"
_TEXT_PREFIX = "sads1:"
_FORM_ENC_KEY = "__sads_enc__"
_NONCE_LEN = 16
_TAG_LEN = 32
_KEY_LEN = 32
_BLOCK = 32  # HMAC-SHA256 output


class CryptoError(RuntimeError):
    """Falha ao cifrar/decifrar dossiê."""


def generate_encryption_key() -> str:
    """Gera chave 32 bytes em base64 url-safe (para colar no .env)."""
    return base64.urlsafe_b64encode(secrets.token_bytes(_KEY_LEN)).decode("ascii")


def _load_key_bytes() -> bytes | None:
    settings = get_settings()
    raw = (getattr(settings, "project_data_encryption_key", None) or "").strip()
    if not raw:
        return None
    try:
        if len(raw) == 64 and all(c in "0123456789abcdefABCDEF" for c in raw):
            key = bytes.fromhex(raw)
        else:
            pad = "=" * (-len(raw) % 4)
            key = base64.urlsafe_b64decode(raw + pad)
    except Exception as exc:  # noqa: BLE001
        raise CryptoError(
            "PROJECT_DATA_ENCRYPTION_KEY invalida (use base64 32 bytes ou hex 64)."
        ) from exc
    if len(key) != _KEY_LEN:
        raise CryptoError(
            f"PROJECT_DATA_ENCRYPTION_KEY deve ter {_KEY_LEN} bytes (obtido {len(key)})."
        )
    return key


def encryption_enabled() -> bool:
    try:
        return _load_key_bytes() is not None
    except CryptoError:
        return False


def _derive_subkeys(key: bytes) -> tuple[bytes, bytes]:
    """Separa chave de cifra e chave de autenticação (HKDF-like simples)."""
    enc = hmac.new(key, b"sads-enc-v1", hashlib.sha256).digest()
    mac = hmac.new(key, b"sads-mac-v1", hashlib.sha256).digest()
    return enc, mac


def _keystream(enc_key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hmac.new(
            enc_key,
            nonce + counter.to_bytes(8, "big"),
            hashlib.sha256,
        ).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def _seal(key: bytes, plaintext: bytes) -> bytes:
    enc_key, mac_key = _derive_subkeys(key)
    nonce = os.urandom(_NONCE_LEN)
    stream = _keystream(enc_key, nonce, len(plaintext))
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream, strict=True))
    tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    return nonce + ciphertext + tag


def _open(key: bytes, blob: bytes) -> bytes:
    if len(blob) < _NONCE_LEN + _TAG_LEN:
        raise CryptoError("Blob cifrado truncado ou invalido.")
    nonce = blob[:_NONCE_LEN]
    tag = blob[-_TAG_LEN:]
    ciphertext = blob[_NONCE_LEN:-_TAG_LEN]
    enc_key, mac_key = _derive_subkeys(key)
    expected = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise CryptoError("Falha ao decifrar (chave errada ou dados corrompidos).")
    stream = _keystream(enc_key, nonce, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, stream, strict=True))


def encrypt_bytes(plaintext: bytes) -> bytes:
    key = _load_key_bytes()
    if key is None:
        return plaintext
    return _FILE_MAGIC + _seal(key, plaintext)


def decrypt_bytes(blob: bytes) -> bytes:
    if not blob.startswith(_FILE_MAGIC):
        return blob
    key = _load_key_bytes()
    if key is None:
        raise CryptoError(
            "Arquivo cifrado encontrado, mas PROJECT_DATA_ENCRYPTION_KEY nao esta definida."
        )
    return _open(key, blob[len(_FILE_MAGIC) :])


def is_encrypted_bytes(blob: bytes) -> bool:
    return blob.startswith(_FILE_MAGIC)


def encrypt_text(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    key = _load_key_bytes()
    if key is None:
        return plaintext
    if plaintext.startswith(_TEXT_PREFIX):
        return plaintext
    sealed = _seal(key, plaintext.encode("utf-8"))
    token = base64.urlsafe_b64encode(sealed).decode("ascii").rstrip("=")
    return _TEXT_PREFIX + token


def decrypt_text(value: str | None) -> str | None:
    if value is None:
        return None
    if not value.startswith(_TEXT_PREFIX):
        return value
    key = _load_key_bytes()
    if key is None:
        raise CryptoError(
            "Texto cifrado encontrado, mas PROJECT_DATA_ENCRYPTION_KEY nao esta definida."
        )
    raw_b64 = value[len(_TEXT_PREFIX) :]
    pad = "=" * (-len(raw_b64) % 4)
    try:
        blob = base64.urlsafe_b64decode(raw_b64 + pad)
    except Exception as exc:  # noqa: BLE001
        raise CryptoError("Texto cifrado com encoding invalido.") from exc
    return _open(key, blob).decode("utf-8")


def is_encrypted_text(value: str | None) -> bool:
    return bool(value and value.startswith(_TEXT_PREFIX))


def encrypt_form_data(data: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(data or {})
    if _load_key_bytes() is None:
        return payload
    if _FORM_ENC_KEY in payload and len(payload) == 1:
        return payload
    sealed = encrypt_text(json.dumps(payload, ensure_ascii=False))
    return {_FORM_ENC_KEY: sealed}


def decrypt_form_data(data: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(data or {})
    if _FORM_ENC_KEY not in payload:
        return payload
    sealed = payload.get(_FORM_ENC_KEY)
    if not isinstance(sealed, str):
        return payload
    plain = decrypt_text(sealed)
    if not plain:
        return {}
    try:
        obj = json.loads(plain)
    except json.JSONDecodeError as exc:
        raise CryptoError("form_data cifrado nao e JSON valido apos decifrar.") from exc
    if not isinstance(obj, dict):
        raise CryptoError("form_data cifrado nao e um objeto JSON.")
    return obj


def write_encrypted_file(path: Path, plaintext: bytes) -> int:
    blob = encrypt_bytes(plaintext)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    return len(blob)


def read_decrypt_file(path: Path) -> bytes:
    return decrypt_bytes(path.read_bytes())
