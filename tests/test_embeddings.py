"""Testes do helper de embeddings (sem baixar modelo HF)."""

import numpy as np

from app.embeddings import EMBEDDING_DIM, HashingEmbedder, chunk_text, vector_to_pg


def test_chunk_text_short() -> None:
    assert chunk_text("abc") == ["abc"]


def test_chunk_text_long() -> None:
    text = "x" * 3500
    chunks = chunk_text(text, chunk_size=1500, overlap=200)
    assert len(chunks) >= 2
    assert all(len(c) <= 1500 for c in chunks)


def test_vector_to_pg_format() -> None:
    s = vector_to_pg([0.1, -0.2, 0.3])
    assert s.startswith("[")
    assert s.endswith("]")
    assert "0.10000000" in s


def test_hashing_embedder_dim() -> None:
    emb = HashingEmbedder()
    vec = emb.embed(["inovacao em editais FINEP"])[0]
    assert len(vec) == EMBEDDING_DIM
    assert abs(float(np.linalg.norm(vec)) - 1.0) < 1e-5
