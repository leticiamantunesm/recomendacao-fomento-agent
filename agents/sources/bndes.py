"""Fonte BNDES — menção ampla (sem catálogo de linhas/programas específicos).

Decisão (ADR-009): a Loja de APIs Developers@BNDES não autorizou o uso das APIs
oficiais de Portfólio/Opções no prazo do TCC. O Navegador lista dezenas de
produtos específicos; o SADS **não** recomenda Finame, Cartão, Mais Inovação etc.
como itens distintos — apenas sinaliza o BNDES como instituição de crédito/
financiamento e aponta o portal oficial para o usuário explorar.

Portal de referência:
  https://www.bndes.gov.br/wps/portal/site/home/financiamento/navegador/#!/
"""

from __future__ import annotations

from pathlib import Path

from agents.sources.base import OpenCall, download_binary

BNDES_BASE = "https://www.bndes.gov.br"
BNDES_NAV_URL = "https://www.bndes.gov.br/wps/portal/site/home/financiamento/navegador/#!/"
BNDES_FINANCING_HOME = f"{BNDES_BASE}/wps/portal/site/home/financiamento/"

# Uma única entrada institucional (não é linha/programa específico).
_BROAD_OPPORTUNITY = OpenCall(
    source="BNDES",
    external_id="bndes-credito-institucional",
    title="BNDES — Crédito e financiamento (consulta ao portal)",
    detail_url=BNDES_NAV_URL,
    situacao="Aberta",
    themes=["crédito", "financiamento", "BNDES", "investimento"],
    opportunity_type="Instituição de crédito/financiamento (visão ampla)",
    region="Brasil",
    description_text=(
        "O BNDES oferece crédito e financiamento a empresas no Brasil. "
        "O SADS não detalha linhas ou programas específicos (Finame, Cartão, "
        "Mais Inovação, etc.): a recomendação é considerar o BNDES como opção "
        "institucional de crédito e consultar o portal oficial / Navegador de "
        f"Financiamentos para escolher o produto adequado. Portal: {BNDES_NAV_URL}"
    ),
    raw={
        "broad_only": True,
        "adr": "ADR-009",
        "portal": BNDES_FINANCING_HOME,
    },
)


class BndesSource:
    """Fonte reduzida: 1 oportunidade ampla, sem scrape de produtos."""

    def close(self) -> None:
        return None

    def __enter__(self) -> BndesSource:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def collect_calls(
        self,
        *,
        limit: int | None = None,
        only_open: bool = True,
        enrich_details: bool = True,
        innovation_only: bool = True,
    ) -> list[OpenCall]:
        del enrich_details, innovation_only  # API/HTML de produtos não usados
        call = OpenCall(
            source=_BROAD_OPPORTUNITY.source,
            external_id=_BROAD_OPPORTUNITY.external_id,
            title=_BROAD_OPPORTUNITY.title,
            detail_url=_BROAD_OPPORTUNITY.detail_url,
            situacao=_BROAD_OPPORTUNITY.situacao,
            themes=list(_BROAD_OPPORTUNITY.themes or []),
            opportunity_type=_BROAD_OPPORTUNITY.opportunity_type,
            region=_BROAD_OPPORTUNITY.region,
            description_text=_BROAD_OPPORTUNITY.description_text,
            raw=dict(_BROAD_OPPORTUNITY.raw or {}),
        )
        if only_open and call.situacao.lower().startswith("encerr"):
            return []
        if limit is not None and limit <= 0:
            return []
        return [call]

    def enrich_call(self, call: OpenCall) -> OpenCall:
        """No-op: não enriquece páginas de produto específico."""
        return call

    def download_attachment(self, att: dict, dest_dir: Path) -> tuple[Path, bool]:
        url = str(att.get("pdf_url") or att.get("url") or "")
        name = str(att.get("pdf_name") or "")
        if not url or not name:
            raise ValueError("anexo BNDES sem pdf_url/pdf_name")
        return download_binary(url, Path(dest_dir) / name)
