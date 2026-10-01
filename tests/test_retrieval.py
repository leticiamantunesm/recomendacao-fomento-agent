"""Testes unitários do Retrieval Agent (sem Neon)."""

from agents.retrieval_agent import CompanyProfile, build_reasons, cosine_similarity_from_distance


def test_cosine_similarity_from_distance() -> None:
    assert abs(cosine_similarity_from_distance(0.0) - 1.0) < 1e-9
    assert abs(cosine_similarity_from_distance(0.25) - 0.75) < 1e-9
    assert cosine_similarity_from_distance(2.0) == 0.0


def test_build_reasons_area_overlap_and_trl() -> None:
    company = CompanyProfile(name="X", size="EPP", trl=6, areas=["inovação", "IA"])
    reasons = build_reasons(
        company=company,
        edict_areas=["Inovação", "Saúde"],
        edict_min_trl=4,
        edict_sizes=["EPP", "ME"],
        agency="FINEP",
        similarity=0.81,
    )
    joined = " | ".join(reasons)
    assert "0.810" in joined or "0.81" in joined
    assert "inovação" in joined.lower()
    assert "TRL" in joined
    assert "EPP" in joined
    assert "FINEP" in joined
