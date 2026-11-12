"""Testes da criptografia at-rest de dossiês."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import get_settings
from app import crypto


@pytest.fixture()
def encryption_key(monkeypatch: pytest.MonkeyPatch) -> str:
    key = crypto.generate_encryption_key()
    monkeypatch.setenv("PROJECT_DATA_ENCRYPTION_KEY", key)
    get_settings.cache_clear()
    yield key
    get_settings.cache_clear()


def test_generate_key_length() -> None:
    key = crypto.generate_encryption_key()
    assert len(key) >= 40


def test_passthrough_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROJECT_DATA_ENCRYPTION_KEY", raising=False)
    get_settings.cache_clear()
    assert crypto.encryption_enabled() is False
    assert crypto.encrypt_text("segredo") == "segredo"
    assert crypto.decrypt_text("segredo") == "segredo"
    blob = b"%PDF-1.4 fake"
    assert crypto.encrypt_bytes(blob) == blob
    get_settings.cache_clear()


def test_roundtrip_text(encryption_key: str) -> None:
    assert crypto.encryption_enabled() is True
    sealed = crypto.encrypt_text("projeto confidencial P&D")
    assert sealed is not None
    assert sealed.startswith("sads1:")
    assert "confidencial" not in sealed
    assert crypto.decrypt_text(sealed) == "projeto confidencial P&D"


def test_roundtrip_bytes_and_file(encryption_key: str, tmp_path: Path) -> None:
    plain = b"%PDF-1.4\nconteudo secreto do projeto"
    sealed = crypto.encrypt_bytes(plain)
    assert sealed.startswith(b"SADS1")
    assert b"secreto" not in sealed
    assert crypto.decrypt_bytes(sealed) == plain

    path = tmp_path / "doc.pdf"
    size = crypto.write_encrypted_file(path, plain)
    assert size == path.stat().st_size
    assert path.read_bytes().startswith(b"SADS1")
    assert crypto.read_decrypt_file(path) == plain


def test_legacy_plaintext_still_reads(encryption_key: str) -> None:
    assert crypto.decrypt_text("texto antigo em claro") == "texto antigo em claro"
    assert crypto.decrypt_bytes(b"%PDF legado") == b"%PDF legado"


def test_form_data_envelope(encryption_key: str) -> None:
    form = {"title": "Projeto X", "summary": "vantagem competitiva"}
    sealed = crypto.encrypt_form_data(form)
    assert list(sealed.keys()) == ["__sads_enc__"]
    assert "vantagem" not in str(sealed)
    opened = crypto.decrypt_form_data(sealed)
    assert opened["title"] == "Projeto X"
    assert opened["summary"] == "vantagem competitiva"


def test_wrong_key_fails(encryption_key: str, monkeypatch: pytest.MonkeyPatch) -> None:
    sealed = crypto.encrypt_text("dados")
    other = crypto.generate_encryption_key()
    monkeypatch.setenv("PROJECT_DATA_ENCRYPTION_KEY", other)
    get_settings.cache_clear()
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt_text(sealed)
    get_settings.cache_clear()
