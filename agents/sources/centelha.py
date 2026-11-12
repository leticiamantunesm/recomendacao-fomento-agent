"""Fonte Programa Centelha — inscricoes abertas por estado.

Portal: https://programacentelha.com.br/
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from agents.sources.base import (
    OpenCall,
    absolute_url,
    clean_text,
    fetch_html,
    slug_id,
)

CENTELHA_URL = "https://programacentelha.com.br/"
CENTELHA_BASE = "https://programacentelha.com.br"


class CentelhaSource:
    def close(self) -> None:
        return None

    def __enter__(self) -> CentelhaSource:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def collect_calls(self, *, limit: int | None = None, only_open: bool = True) -> list[OpenCall]:
        html = fetch_html(CENTELHA_URL)
        soup = BeautifulSoup(html, "html.parser")
        calls: list[OpenCall] = []
        seen: set[str] = set()

        open_states = self._states_with_open_inscriptions(soup, html)
        if not open_states and not only_open:
            open_states = self._all_state_links(soup)

        for name, href in open_states:
            uf = self._extract_uf(name, href)
            title = f"Programa Centelha 3 — {name}"
            ext = slug_id("centelha", uf or name)
            if ext in seen:
                continue
            seen.add(ext)
            url = absolute_url(CENTELHA_BASE, href)
            description = (
                f"Programa Centelha (empreendedorismo inovador). "
                f"Inscrições abertas para o estado/região: {name}. "
                "Apoia ideias inovadoras com subvenção econômica, capacitação e suporte técnico. "
                "Não é obrigatório ter CNPJ na submissão inicial. "
                f"Detalhes e edital estadual: {url}"
            )
            calls.append(
                OpenCall(
                    source="CENTELHA",
                    external_id=ext,
                    title=title[:300],
                    detail_url=url,
                    situacao="Aberta",
                    themes=["startup", "empreendedorismo", "inovação", "subvenção"],
                    opportunity_type="Subvenção econômica / Centelha",
                    region=uf or name,
                    description_text=description,
                    raw={"estado": name, "uf": uf},
                )
            )
            if limit is not None and len(calls) >= limit:
                break

        # Sempre inclui oportunidade nacional de referencia (portal).
        if limit is None or len(calls) < limit:
            national_id = "centelha-nacional"
            if national_id not in seen and open_states:
                calls.append(
                    OpenCall(
                        source="CENTELHA",
                        external_id=national_id,
                        title="Programa Centelha 3 — portal nacional",
                        detail_url=CENTELHA_URL,
                        situacao="Aberta",
                        themes=["startup", "empreendedorismo", "inovação"],
                        opportunity_type="Subvenção econômica / Centelha",
                        region="Brasil",
                        description_text=(
                            "Portal nacional do Programa Centelha 3. "
                            "Execução descentralizada pelas FAPs estaduais. "
                            f"Estados com inscrição em destaque na home: "
                            f"{', '.join(n for n, _ in open_states)}."
                        ),
                        raw={"estados_abertos": [n for n, _ in open_states]},
                    )
                )
        return calls

    def _states_with_open_inscriptions(
        self, soup: BeautifulSoup, html: str
    ) -> list[tuple[str, str]]:
        """Extrai estados no bloco 'INSCRIÇÕES ABERTAS' da home."""
        found: list[tuple[str, str]] = []
        # Procura containers próximos ao texto.
        for node in soup.find_all(string=re.compile(r"INSCRI", re.I)):
            parent = node.parent
            for _ in range(6):
                if parent is None:
                    break
                for a in parent.find_all("a", href=True):
                    name = clean_text(a.get_text(" ", strip=True))
                    href = a["href"]
                    if not name or len(name) > 60:
                        continue
                    if "material" in href or href.rstrip("/").endswith("programacentelha.com.br"):
                        # link curto tipo /al
                        pass
                    if self._looks_like_state(name, href):
                        found.append((name, href))
                parent = parent.parent
            if found:
                break

        # Dedup
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for name, href in found:
            key = href.rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            out.append((name, href))
        return out

    def _all_state_links(self, soup: BeautifulSoup) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            name = clean_text(a.get_text(" ", strip=True))
            href = a["href"]
            if not self._looks_like_state(name, href):
                continue
            key = href.rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            out.append((name, href))
        return out

    @staticmethod
    def _looks_like_state(name: str, href: str) -> bool:
        if re.search(r"\(([A-Z]{2})\)$", name):
            return True
        if re.search(r"programacentelha\.com\.br/[a-z]{2}/?$", href, flags=re.I):
            return True
        if "materiais.programacentelha.com.br" in href and len(name) < 40:
            return True
        known = {
            "acre",
            "alagoas",
            "amapá",
            "amapa",
            "amazonas",
            "bahia",
            "ceará",
            "ceara",
            "distrito federal",
            "espírito santo",
            "espirito santo",
            "goiás",
            "goias",
            "maranhão",
            "maranhao",
            "mato grosso",
            "mato grosso do sul",
            "minas gerais",
            "pará",
            "para",
            "paraíba",
            "paraiba",
            "paraná",
            "parana",
            "pernambuco",
            "piauí",
            "piaui",
            "rio de janeiro",
            "rio grande do norte",
            "rio grande do sul",
            "rondônia",
            "rondonia",
            "roraima",
            "santa catarina",
            "são paulo",
            "sao paulo",
            "sergipe",
            "tocantins",
        }
        return name.lower() in known

    @staticmethod
    def _extract_uf(name: str, href: str) -> str | None:
        m = re.search(r"\(([A-Z]{2})\)$", name)
        if m:
            return m.group(1)
        m = re.search(r"/([a-z]{2})/?$", href.rstrip("/"), flags=re.I)
        if m:
            return m.group(1).upper()
        return None
