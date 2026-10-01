"""Agente de Adequação e Busca (Retrieval) — T-030.

Busca híbrida: filtros SQL (elegibilidade) + ranking por similaridade de cosseno (pgvector).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from sqlalchemy import text

from app.embeddings import embed_text, get_embedder, vector_to_pg
from db.session import dispose_engine, session_scope


@dataclass
class CompanyProfile:
    """Perfil usado nos filtros de elegibilidade."""

    name: str = "Empresa Demo"
    size: str | None = None  # MEI/ME/EPP/Grande
    trl: int | None = None
    areas: list[str] = field(default_factory=list)
    uf: str | None = None


@dataclass
class ProjectQuery:
    """Texto/projeto a cruzar semanticamente com editais."""

    title: str
    text: str
    budget_brl: float | str | None = None


@dataclass
class EdictMatch:
    external_id: str | None
    title: str
    agency: str | None
    year: int | None
    areas: list[str]
    url: str | None
    distance: float
    similarity: float
    reasons: list[str]
    excerpt: str = ""
    min_trl: int | None = None
    company_sizes: list[str] = field(default_factory=list)
    region: str | None = None
    prazo_proposta: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalResult:
    matches: list[EdictMatch]
    filters_applied: dict[str, Any]
    query_title: str
    backend: str
    candidate_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_title": self.query_title,
            "backend": self.backend,
            "filters_applied": self.filters_applied,
            "candidate_count": self.candidate_count,
            "matches": [m.to_dict() for m in self.matches],
        }


def cosine_similarity_from_distance(distance: float) -> float:
    """Com vetores L2-normalizados, distância de cosseno do pgvector ≈ 1 - cos_sim."""
    return max(0.0, min(1.0, 1.0 - float(distance)))


def build_reasons(
    *,
    company: CompanyProfile,
    edict_areas: Sequence[str],
    edict_min_trl: int | None,
    edict_sizes: Sequence[str],
    agency: str | None,
    similarity: float,
) -> list[str]:
    reasons: list[str] = []
    reasons.append(f"Similaridade semantica (cosseno) ~= {similarity:.3f}")

    company_areas = {a.lower() for a in company.areas if a}
    edict_area_set = {a.lower() for a in edict_areas if a}
    overlap = sorted(company_areas & edict_area_set)
    if overlap:
        reasons.append(f"Sobreposição de áreas: {', '.join(overlap)}")
    elif edict_areas:
        reasons.append(f"Áreas do edital: {', '.join(edict_areas[:5])}")

    if company.trl is not None and edict_min_trl is not None:
        if company.trl >= edict_min_trl:
            reasons.append(f"TRL da empresa ({company.trl}) ≥ mínimo do edital ({edict_min_trl})")
        else:
            reasons.append(
                f"Atenção: TRL da empresa ({company.trl}) < mínimo do edital ({edict_min_trl})"
            )
    elif edict_min_trl is None:
        reasons.append("Edital sem TRL mínimo cadastrado (filtro TRL não restritivo)")

    if company.size and edict_sizes:
        if company.size in edict_sizes:
            reasons.append(f"Porte {company.size} elegível no edital")
        else:
            reasons.append(
                f"Atenção: porte {company.size} não listado em {', '.join(edict_sizes)}"
            )
    elif not edict_sizes:
        reasons.append("Edital sem restrição explícita de porte no cadastro")

    if agency:
        reasons.append(f"Órgão/fonte: {agency}")

    return reasons


class RetrievalAgent:
    """Cruzamento projeto/empresa × editais indexados (híbrido SQL + vetor)."""

    def __init__(self) -> None:
        self._embedder = None

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    async def retrieve(
        self,
        project: ProjectQuery,
        company: CompanyProfile,
        *,
        k: int = 5,
        agency: str | None = None,
        year: int | None = None,
        require_area_overlap: bool = False,
        enforce_trl: bool = False,
        enforce_size: bool = False,
    ) -> RetrievalResult:
        """
        1) Filtra candidatos no SQL (quando houver metadados).
        2) Ordena por distância de cosseno entre embedding(projeto) e edicts.embedding.
        3) Devolve top-k com razões de adequação.
        """
        query_blob = f"{project.title}\n\n{project.text}".strip()
        vector = embed_text(query_blob, embedder=self.embedder)
        literal = vector_to_pg(vector)
        backend = getattr(self.embedder, "name", "unknown")

        where = ["e.embedding IS NOT NULL", "e.raw_text IS NOT NULL"]
        params: dict[str, Any] = {"q": literal, "k": k}

        if agency:
            where.append("e.agency ILIKE :agency")
            params["agency"] = f"%{agency}%"

        if year is not None:
            where.append("(e.year IS NULL OR e.year = :year)")
            params["year"] = year

        if require_area_overlap and company.areas:
            where.append("e.areas && CAST(:areas AS text[])")
            params["areas"] = company.areas

        if enforce_trl and company.trl is not None:
            where.append("(e.min_trl IS NULL OR e.min_trl <= :trl)")
            params["trl"] = company.trl

        if enforce_size and company.size:
            where.append(
                "(cardinality(e.company_sizes) = 0 OR :size = ANY(e.company_sizes))"
            )
            params["size"] = company.size

        where_sql = " AND ".join(where)
        sql = text(
            f"""
            SELECT
              e.external_id,
              e.title,
              e.agency,
              e.year,
              e.areas,
              e.min_trl,
              e.company_sizes,
              e.url,
              e.metadata->>'region' AS region,
              e.metadata->>'prazo_proposta' AS prazo_proposta,
              left(e.raw_text, 400) AS excerpt,
              (e.embedding <=> CAST(:q AS vector)) AS distance
            FROM edicts e
            WHERE {where_sql}
            ORDER BY e.embedding <=> CAST(:q AS vector)
            LIMIT :k
            """
        )

        filters_applied = {
            "agency": agency,
            "year": year,
            "require_area_overlap": require_area_overlap,
            "enforce_trl": enforce_trl,
            "enforce_size": enforce_size,
            "company_areas": company.areas,
            "company_size": company.size,
            "company_trl": company.trl,
            "k": k,
        }

        async with session_scope() as session:
            count_sql = text(f"SELECT count(*) FROM edicts e WHERE {where_sql}")
            count_params = {key: val for key, val in params.items() if key not in {"q", "k"}}
            candidate_count = int((await session.execute(count_sql, count_params)).scalar_one())
            rows = (await session.execute(sql, params)).mappings().all()

        matches: list[EdictMatch] = []
        for row in rows:
            distance = float(row["distance"])
            similarity = cosine_similarity_from_distance(distance)
            areas = list(row["areas"] or [])
            sizes = list(row["company_sizes"] or [])
            matches.append(
                EdictMatch(
                    external_id=row["external_id"],
                    title=row["title"],
                    agency=row["agency"],
                    year=row["year"],
                    areas=areas,
                    url=row["url"],
                    distance=distance,
                    similarity=similarity,
                    reasons=build_reasons(
                        company=company,
                        edict_areas=areas,
                        edict_min_trl=row["min_trl"],
                        edict_sizes=sizes,
                        agency=row["agency"],
                        similarity=similarity,
                    ),
                    excerpt=(row["excerpt"] or "").replace("\n", " ").strip(),
                    min_trl=row["min_trl"],
                    company_sizes=sizes,
                    region=row.get("region"),
                    prazo_proposta=row.get("prazo_proposta"),
                )
            )

        await dispose_engine()
        return RetrievalResult(
            matches=matches,
            filters_applied=filters_applied,
            query_title=project.title,
            backend=backend,
            candidate_count=candidate_count,
        )
