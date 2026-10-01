"""Testes unitarios da fonte FINEP (sem rede)."""

from agents.sources.finep import (
    _classify_role,
    _is_open,
    _list_pdf_attachments,
    _matches_situacao,
    _pick_pdf,
    _slug_filename,
    _theme_names,
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
