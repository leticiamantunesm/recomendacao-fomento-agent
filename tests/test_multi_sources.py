"""Testes das fontes HTML (fixtures locais, sem rede)."""

from __future__ import annotations

from pathlib import Path

from agents.sources.bndes import BndesSource
from agents.sources.centelha import CentelhaSource
from agents.sources.cnpq import CnpqSource
from agents.sources.embrapii import EmbrapiiSource
from agents.sources.fapesp import FapespSource

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "portals"


def test_cnpq_parses_open_calls(monkeypatch) -> None:
    html = (FIXTURES / "cnpq.html").read_text(encoding="utf-8", errors="ignore")
    monkeypatch.setattr("agents.sources.cnpq.fetch_html", lambda url, client=None: html)
    with CnpqSource() as source:
        calls = source.collect_calls(only_open=False)
    assert len(calls) >= 5
    assert all(c.source == "CNPQ" for c in calls)
    assert any("MAI/DAI" in c.title or "Inspir" in c.title for c in calls)
    assert any(c.prazo_proposta for c in calls)


def test_fapesp_parses_open_calls(monkeypatch) -> None:
    html = (FIXTURES / "fapesp.html").read_text(encoding="utf-8", errors="ignore")
    monkeypatch.setattr("agents.sources.fapesp.fetch_html", lambda url, client=None: html)
    with FapespSource() as source:
        calls = source.collect_calls(only_open=False, enrich_details=False)
    assert len(calls) >= 5
    assert all(c.source == "FAPESP" for c in calls)
    assert any(c.external_id.startswith("fapesp-") and c.external_id.split("-")[1].isdigit() for c in calls)
    assert any("PIPE" in c.title.upper() or "pipe" in (c.opportunity_type or "").lower() for c in calls)


def test_fapesp_enriches_detail_and_attachments(monkeypatch) -> None:
    listing = (FIXTURES / "fapesp.html").read_text(encoding="utf-8", errors="ignore")
    redirect = (FIXTURES / "fapesp_redirect.html").read_text(encoding="utf-8")
    detail = (FIXTURES / "fapesp_detail.html").read_text(encoding="utf-8")

    def fake_fetch(url, client=None):
        if "chamadas" in url and url.rstrip("/").endswith("chamadas"):
            return listing
        if url.rstrip("/").endswith("/18434") or url.endswith("fapesp.br/18434"):
            return redirect
        if "18434/" in url or "tecnologias-educacionais" in url:
            return detail
        return listing

    monkeypatch.setattr("agents.sources.fapesp.fetch_html", fake_fetch)
    with FapespSource() as source:
        calls = source.collect_calls(limit=3, only_open=False, enrich_details=True)

    pipe = next(c for c in calls if c.external_id == "fapesp-18434")
    assert "recursos não reembolsáveis" in pipe.description_text
    assert pipe.published_at and pipe.published_at.startswith("2026-10-05")
    assert any(a.get("pdf_name", "").endswith(".pdf") for a in pipe.attachments)
    assert any("anexo1.docx" in (a.get("pdf_url") or "") for a in pipe.attachments)
    assert not any("csc.pdf" in (a.get("pdf_url") or "") for a in pipe.attachments)


def test_centelha_open_states_from_html(monkeypatch) -> None:
    html = """
    <html><body>
      <p>INSCRIÇÕES ABERTAS:</p>
      <a href="https://materiais.programacentelha.com.br/al">Alagoas</a>
      <div class="states">
        <a href="https://programacentelha.com.br/mg/">Minas Gerais (MG)</a>
        <a href="https://programacentelha.com.br/sp/">São Paulo (SP)</a>
      </div>
    </body></html>
    """
    monkeypatch.setattr("agents.sources.centelha.fetch_html", lambda url, client=None: html)
    with CentelhaSource() as source:
        calls = source.collect_calls()
    assert calls
    assert any("Alagoas" in c.title or c.region == "AL" for c in calls)
    assert all(c.source == "CENTELHA" for c in calls)


def test_embrapii_areas_and_calls(monkeypatch) -> None:
    areas = """
    <html><body>
      <select>
        <option>Selecione</option>
        <option>BIOTECNOLOGIA</option>
        <option>Sistemas Embarcados</option>
        <option>Competências Tecnológicas</option>
      </select>
    </body></html>
    """
    listing = (FIXTURES / "embrapii_transparencia.html").read_text(encoding="utf-8")

    def fake_fetch(url, client=None):
        if "areas-de-atuacao" in url:
            return areas
        return listing

    monkeypatch.setattr("agents.sources.embrapii.fetch_html", fake_fetch)
    with EmbrapiiSource() as source:
        calls = source.collect_calls(enrich_details=False, include_areas=True)
    assert any(c.opportunity_type and "fluxo contínuo" in c.opportunity_type for c in calls)
    assert any("Economia Circular" in c.title for c in calls)
    assert any(c.external_id.startswith("embrapii-chamada-publica-n02-2026") for c in calls)


def test_embrapii_enriches_detail_and_attachments(monkeypatch) -> None:
    listing = (FIXTURES / "embrapii_transparencia.html").read_text(encoding="utf-8")
    detail = (FIXTURES / "embrapii_detail.html").read_text(encoding="utf-8")
    areas = "<html><body><select><option>Selecione</option></select></body></html>"

    def fake_fetch(url, client=None):
        if "areas-de-atuacao" in url:
            return areas
        if "transparencia" in url:
            return listing
        if "economia-circular" in url:
            return detail
        return "<html><body><h1>Outra</h1><div class='chamadas-publicas-content'>x" + ("y" * 300) + "</div></body></html>"

    monkeypatch.setattr("agents.sources.embrapii.fetch_html", fake_fetch)
    with EmbrapiiSource() as source:
        calls = source.collect_calls(
            limit=3,
            only_open=True,
            enrich_details=True,
            include_areas=False,
        )
    call = next(c for c in calls if "economia-circular" in c.detail_url)
    assert "Petrobras" in call.description_text or "Economia Circular" in call.description_text
    assert any(
        (a.get("pdf_url") or "").endswith("economia-circular.pdf") for a in call.attachments
    )
    assert not any("sharepoint" in (a.get("pdf_url") or "") for a in call.attachments)
    assert calls[0].external_id.startswith("embrapii-chamada-publica-n02-2026")


def test_bndes_broad_institutional_only() -> None:
    """ADR-009: uma entrada ampla — sem catálogo de linhas/programas."""
    with BndesSource() as source:
        calls = source.collect_calls(enrich_details=False)
    assert len(calls) == 1
    call = calls[0]
    assert call.source == "BNDES"
    assert call.external_id == "bndes-credito-institucional"
    assert "Finame" not in (call.title or "")
    assert "Mais Inovação" not in (call.title or "")
    assert "Cartão" not in (call.title or "")
    assert "navegador" in (call.description_text or "").lower() or "portal" in (
        call.description_text or ""
    ).lower()
    assert (call.raw or {}).get("broad_only") is True


def test_bndes_limit_zero() -> None:
    with BndesSource() as source:
        assert source.collect_calls(limit=0) == []
