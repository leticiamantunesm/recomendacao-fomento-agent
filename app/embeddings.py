"""Utilitários de embeddings — T-020.

Primary: sentence-transformers (MiniLM, dim 384).
Fallback offline: HashingVectorizer → 384 dims (rede corporativa / sem HuggingFace).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Protocol

import numpy as np

from app.config import get_settings

EMBEDDING_DIM = 384


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    name = "sentence-transformers"

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float64)


class HashingEmbedder:
    """Fallback determinístico sem download (útil atrás de proxy/firewall)."""

    name = "hashing-vectorizer"

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        from sklearn.feature_extraction.text import HashingVectorizer

        self.vectorizer = HashingVectorizer(
            n_features=dim,
            alternate_sign=False,
            norm="l2",
            ngram_range=(1, 2),
            lowercase=True,
        )

    def embed(self, texts: list[str]) -> np.ndarray:
        matrix = self.vectorizer.transform(texts)
        dense = matrix.toarray().astype(np.float64)
        # garantir L2
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return dense / norms


@lru_cache
def get_embedder(model_name: str | None = None) -> Embedder:
    settings = get_settings()
    name = model_name or settings.embedding_model_name
    backend = (getattr(settings, "embedding_backend", None) or "auto").lower()

    if backend in {"hash", "hashing", "offline"}:
        print("Embeddings: usando HashingVectorizer (offline).")
        return HashingEmbedder()

    if backend in {"st", "sentence-transformers", "auto"}:
        try:
            print(f"Embeddings: tentando sentence-transformers ({name})...")
            embedder = SentenceTransformerEmbedder(name)
            print("Embeddings: sentence-transformers OK.")
            return embedder
        except Exception as exc:  # noqa: BLE001
            if backend != "auto":
                raise
            print(f"Embeddings: falha ao carregar MiniLM ({exc}).")
            print("Embeddings: fallback HashingVectorizer (dim 384, offline).")
            return HashingEmbedder()

    raise ValueError(f"EMBEDDING_BACKEND inválido: {backend}")


def chunk_text(text: str, *, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def embed_text(text: str, *, embedder: Embedder | None = None) -> list[float]:
    """Gera vetor L2-normalizado (dim 384). Textos longos: média dos chunks."""
    embedder = embedder or get_embedder()
    chunks = chunk_text(text)
    if not chunks:
        return [0.0] * EMBEDDING_DIM

    vectors = embedder.embed(chunks)
    if len(chunks) == 1:
        vec = vectors[0]
    else:
        vec = vectors.mean(axis=0)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
    out = vec.tolist()
    if len(out) != EMBEDDING_DIM:
        raise ValueError(f"Dimensão inesperada: {len(out)} (esperado {EMBEDDING_DIM})")
    return out


def vector_to_pg(vector: list[float]) -> str:
    """Literal pgvector: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{x:.8f}" for x in vector) + "]"


# compat com imports antigos
def get_embedding_model(model_name: str | None = None) -> Any:
    return get_embedder(model_name)
