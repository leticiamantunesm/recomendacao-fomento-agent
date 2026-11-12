"""Pacote de fontes do Agente Coletor (FINEP + multi-fonte)."""

from __future__ import annotations

from typing import Any, Callable

from agents.sources.base import OpenCall
from agents.sources.bndes import BndesSource
from agents.sources.centelha import CentelhaSource
from agents.sources.cnpq import CnpqSource
from agents.sources.embrapii import EmbrapiiSource
from agents.sources.fapesp import FapespSource
from agents.sources.finep import FinepSource

HTML_SOURCES: dict[str, Callable[[], Any]] = {
    "fapesp": FapespSource,
    "cnpq": CnpqSource,
    "centelha": CentelhaSource,
    "embrapii": EmbrapiiSource,
    "bndes": BndesSource,
}

ALL_SOURCE_NAMES = ("finep", "fapesp", "cnpq", "centelha", "embrapii", "bndes")


def collect_html_source(
    name: str,
    *,
    limit: int | None = None,
    only_open: bool = True,
) -> list[OpenCall]:
    key = name.strip().lower()
    if key not in HTML_SOURCES:
        raise ValueError(f"Fonte HTML desconhecida: {name}. Opcoes: {sorted(HTML_SOURCES)}")
    cls = HTML_SOURCES[key]
    with cls() as source:
        return source.collect_calls(limit=limit, only_open=only_open)


__all__ = [
    "OpenCall",
    "FinepSource",
    "FapespSource",
    "CnpqSource",
    "CentelhaSource",
    "EmbrapiiSource",
    "BndesSource",
    "HTML_SOURCES",
    "ALL_SOURCE_NAMES",
    "collect_html_source",
]
