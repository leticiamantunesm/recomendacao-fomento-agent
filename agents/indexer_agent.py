"""Agente Indexador — embeddings → pgvector (T-020)."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import text

from app.embeddings import EMBEDDING_DIM, embed_text, get_embedder, vector_to_pg
from db.session import dispose_engine, session_scope


@dataclass
class IndexResult:
    indexed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    backend: str = ""

    @property
    def ok_count(self) -> int:
        return len(self.indexed)


class IndexerAgent:
    """Lê edicts com raw_text e grava embedding vector(384)."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name
        self._embedder = None

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = get_embedder(self.model_name)
        return self._embedder

    async def index_edicts(self, *, only_missing: bool = True, limit: int | None = None) -> IndexResult:
        result = IndexResult()
        async with session_scope() as session:
            if only_missing:
                sql = text(
                    """
                    SELECT id::text, external_id, title, raw_text
                    FROM edicts
                    WHERE raw_text IS NOT NULL
                      AND length(raw_text) >= 500
                      AND embedding IS NULL
                    ORDER BY created_at
                    """
                )
            else:
                sql = text(
                    """
                    SELECT id::text, external_id, title, raw_text
                    FROM edicts
                    WHERE raw_text IS NOT NULL
                      AND length(raw_text) >= 500
                    ORDER BY created_at
                    """
                )
            rows = (await session.execute(sql)).mappings().all()
            if limit is not None:
                rows = rows[:limit]

            if not rows:
                print("Nenhum edital pendente de indexação.")
                return result

            embedder = self.embedder
            result.backend = getattr(embedder, "name", "unknown")
            print(f"Backend={result.backend} Dim={EMBEDDING_DIM} Pendentes={len(rows)}")

            for row in rows:
                external_id = row["external_id"] or row["id"]
                try:
                    vector = embed_text(row["raw_text"], embedder=embedder)
                    literal = vector_to_pg(vector)
                    await session.execute(
                        text(
                            """
                            UPDATE edicts
                            SET embedding = CAST(:embedding AS vector)
                            WHERE id = CAST(:id AS uuid)
                            """
                        ),
                        {"embedding": literal, "id": row["id"]},
                    )
                    result.indexed.append(str(external_id))
                    print(f"  OK  {external_id}")
                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"{external_id}: {exc}")
                    print(f"  FAIL {external_id}: {exc}")

            await session.commit()

            # índice cosine (HNSW; se falhar, tenta ivfflat)
            try:
                await session.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS idx_edicts_embedding_cosine
                        ON edicts USING hnsw (embedding vector_cosine_ops)
                        """
                    )
                )
                await session.commit()
                print("Índice HNSW cosine: OK")
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                print(f"HNSW indisponível ({exc}); tentando ivfflat...")
                try:
                    await session.execute(
                        text(
                            """
                            CREATE INDEX IF NOT EXISTS idx_edicts_embedding_cosine
                            ON edicts USING ivfflat (embedding vector_cosine_ops)
                            WITH (lists = 10)
                            """
                        )
                    )
                    await session.commit()
                    print("Índice ivfflat cosine: OK")
                except Exception as exc2:  # noqa: BLE001
                    await session.rollback()
                    print(f"Índice vetorial não criado (ok no MVP pequeno): {exc2}")

            stats = await session.execute(
                text(
                    """
                    SELECT
                      count(*) FILTER (WHERE embedding IS NOT NULL) AS with_emb,
                      count(*) AS total
                    FROM edicts
                    """
                )
            )
            with_emb, total = stats.one()
            print(f"edicts com embedding: {with_emb}/{total}")

        await dispose_engine()
        return result

    async def smoke_similarity(self, query_text: str, *, k: int = 5) -> list[dict]:
        """Busca top-k por distância de cosseno (<=>)."""
        vector = embed_text(query_text, embedder=self.embedder)
        literal = vector_to_pg(vector)
        async with session_scope() as session:
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT external_id, title, agency,
                               (embedding <=> CAST(:q AS vector)) AS distance
                        FROM edicts
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> CAST(:q AS vector)
                        LIMIT :k
                        """
                    ),
                    {"q": literal, "k": k},
                )
            ).mappings().all()
        await dispose_engine()
        return [dict(r) for r in rows]
