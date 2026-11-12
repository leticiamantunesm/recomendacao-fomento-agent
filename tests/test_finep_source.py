"""Testes unitarios da fonte FINEP (sem rede)."""

from datetime import datetime, timezone

from agents.sources.finep import (
    _classify_role,
    _is_open,
    _list_pdf_attachments,
    _matches_situacao,
    _pick_pdf,
    _slug_filename,
    _theme_names,
    is_item_vigente,
    is_metadata_vigente,
    is_vigente,
    parse_finep_datetime,
)


def test_is_open_aberta() -> None:
    assert _is_open({"situacao": {"name": "Aberta", "key": "aberta"}})
    assert not _is_open({"situacao": {"name": "Encerrada"}})


def test_matches_situacao() -> None:
    aberta = {"situacao": {"name": "Aberta"}}
    encerrada = {"situacao": {"name": "Encerrada"}}
    assert _matches_situacao(aberta, "aberta")
    assert _matches_situacao(aberta, "todas")
    assert _matches_situacao(encerrada, "encerrada")
    assert not _matches_situacao(encerrada, "aberta")


def test_vigente_rejects_expired_prazo_even_if_aberta() -> None:
    now = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
    item = {
        "situacao": {"name": "Aberta"},
        "vigenciaInicio": "2026-08-01T00:00:00.000Z",
        "vigenciaFim": "2027-02-01T00:00:00.000Z",
        "prazoProposto": "2026-09-09T13:00:00.000Z",  # vencido
    }
    assert _matches_situacao(item, "aberta")
    assert not _matches_situacao(item, "vigente")
    assert not is_item_vigente(item, now=now)


def test_vigente_accepts_open_window() -> None:
    now = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
    item = {
        "situacao": {"name": "Aberta"},
        "vigenciaInicio": "2026-10-21T00:00:00.000Z",
        "vigenciaFim": "2027-01-29T00:00:00.000Z",
        "prazoProposto": "2026-11-23T17:00:00.000Z",
    }
    assert is_item_vigente(item, now=now)
    assert _matches_situacao(item, "vigente")


def test_metadata_vigente_and_parse() -> None:
    now = datetime(2026, 11, 9, tzinfo=timezone.utc)
    assert parse_finep_datetime("2026-11-23T17:00:00.000Z") is not None
    assert is_vigente(
        situacao="Aberta",
        prazo_proposta="2026-11-23T17:00:00.000Z",
        now=now,
    )
    assert not is_metadata_vigente(
        {
            "situacao": "Encerrada",
            "prazo_proposta": "2027-01-01T00:00:00.000Z",
        },
        now=now,
    )


def test_pick_pdf_prefers_edital() -> None:
    docs = [
        {
            "legenda": "FAQ",
            "documentoProprietario": {
                "name": "FAQ.pdf",
                "link": {"href": "/documents/faq.pdf"},
            },
        },
        {
            "legenda": "Edital",
            "documentoProprietario": {
                "name": "Edital Final.pdf",
                "link": {"href": "/documents/edital.pdf"},
            },
        },
    ]
    picked = _pick_pdf(docs)
    assert picked is not None
    url, name, legenda = picked
    assert "edital.pdf" in url.lower()
    assert "Edital" in name or "edital" in name.lower()
    assert "Edital" in legenda


def test_list_attachments_all_pdfs() -> None:
    docs = [
        {
            "legenda": "Anexo I",
            "documentoProprietario": {
                "name": "Anexo1.pdf",
                "link": {"href": "/documents/a1.pdf"},
            },
        },
        {
            "legenda": "Edital",
            "documentoProprietario": {
                "name": "Edital.pdf",
                "link": {"href": "/documents/edital.pdf"},
            },
        },
    ]
    atts = _list_pdf_attachments(docs, 99)
    assert len(atts) == 2
    assert atts[0].role == "edital"
    assert "finep_99_" in atts[0].pdf_name


def test_classify_role() -> None:
    assert _classify_role("x.pdf", "Edital completo") == "edital"
    assert _classify_role("faq.pdf", "FAQ") == "faq"
    assert _classify_role("a.pdf", "Anexo II") == "anexo"


def test_theme_names_taxonomy() -> None:
    item = {
        "temaPrincipal": {"name": "Energia"},
        "taxonomyCategoryBriefs": [{"taxonomyCategoryName": "Mobilidade"}],
    }
    themes = _theme_names(item)
    assert "Energia" in themes
    assert "Mobilidade" in themes


def test_slug_filename() -> None:
    name = _slug_filename("Edital - Etapa Nacional.pdf", 1019381)
    assert name.startswith("finep_1019381_")
    assert name.lower().endswith(".pdf")
