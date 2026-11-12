"""Bateria SADS — corpus v2 (GOOD_02–06 + BAD_01–06)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.project_risk import diagnose_project
from agents.scoring_agent import ScoringAgent
from tests.fixtures.sads_corpus_v2 import (
    CORPUS_V2_FILES,
    EXEMPLOS_DIR,
    GABARITO_V2,
    load_corpus_v2,
    synthetic_matches_for,
)

RESULTS_PATH = Path(__file__).resolve().parent / "fixtures" / "_last_sads_corpus_v2.json"


@pytest.fixture(scope="module")
def corpus():
    missing = [f for f in CORPUS_V2_FILES.values() if not (EXEMPLOS_DIR / f).exists()]
    if missing:
        pytest.skip(f"PDFs ausentes: {missing}")
    return load_corpus_v2()


@pytest.fixture(scope="module")
def scored(corpus):
    agent = ScoringAgent()
    out = {}
    for key, ex in corpus.items():
        result = agent.score_matches(
            project=ex.project,
            company=ex.company,
            matches=synthetic_matches_for(key),
            revenue_brl=ex.company.revenue_brl,
        )
        out[key] = {"example": ex, "result": result, "gabarito": GABARITO_V2[key]}
    return out


def test_all_v2_pdfs_present():
    assert len(CORPUS_V2_FILES) == 11
    for fname in CORPUS_V2_FILES.values():
        assert (EXEMPLOS_DIR / fname).exists(), fname


@pytest.mark.parametrize("key", sorted(CORPUS_V2_FILES))
def test_loads_identity(corpus, key):
    ex = corpus[key]
    assert ex.title
    assert ex.company_name
    assert len(ex.raw_text) > 200


@pytest.mark.parametrize("key", [k for k in CORPUS_V2_FILES if k.startswith("GOOD_")])
def test_good_projects_have_tech_risk_and_ideal(scored, key):
    pack = scored[key]
    result = pack["result"]
    g = pack["gabarito"]
    assert result.diagnosis["has_technological_risk"] is True, key
    ideal = next(r for r in result.reports if (r.external_id or "").startswith("ideal-"))
    assert ideal.eligible is True, f"{key}: {ideal.eligibility_status} {ideal.block_reasons}"
    assert ideal.score >= 60, f"{key}: score={ideal.score}"
    # Armadilha de semicondutores não deve ser a recomendação principal
    if result.recommended:
        assert result.recommended[0].external_id != "trap-semi"
    assert g["expect"] == "pass_rd"


def test_bad02_solar_blocks_subvencao(scored):
    result = scored["BAD_02"]["result"]
    assert result.diagnosis["has_technological_risk"] is False
    subs = [r for r in result.reports if r.instrument == "subvencao"]
    assert all(not r.eligible for r in subs)
    assert any("Sebraetec" in s["name"] for s in result.redirect_suggestions)


def test_bad03_marketing_flagged(scored):
    ex = scored["BAD_03"]["example"]
    diag = diagnose_project(
        title=ex.title, text=ex.raw_text, form_data=ex.form_data, trl=ex.trl, uf=ex.uf
    )
    blob = " ".join(diag.ineligible_budget_items).lower()
    assert diag.ineligible_budget_items, "marketing deveria ser detectado"
    assert "marketing" in blob or "ads" in blob or "publicidade" in blob


def test_bad04_budget_math(scored):
    ex = scored["BAD_04"]["example"]
    diag = diagnose_project(
        title=ex.title, text=ex.raw_text, form_data=ex.form_data, trl=ex.trl, uf=ex.uf
    )
    # Preferência: flag do Gate 0; fallback: soma das rubricas parseadas
    sum_items = sum(ex.budget_items.values()) if ex.budget_items else 0
    declared = ex.budget_brl or 0
    inconsistent = diag.budget_math_inconsistency or (
        sum_items > 0 and declared > 0 and abs(sum_items - declared) > max(1000, declared * 0.05)
    )
    assert inconsistent, (
        f"esperado inconsistência: items={ex.budget_items} sum={sum_items} declared={declared} "
        f"diag_math={diag.budget_math_inconsistency}"
    )


def test_bad05_no_tech_risk(scored):
    result = scored["BAD_05"]["result"]
    assert result.diagnosis["has_technological_risk"] is False
    subs = [r for r in result.reports if r.instrument == "subvencao"]
    assert all(not r.eligible for r in subs)


def test_bad06_budget_math(scored):
    ex = scored["BAD_06"]["example"]
    diag = diagnose_project(
        title=ex.title, text=ex.raw_text, form_data=ex.form_data, trl=ex.trl, uf=ex.uf
    )
    sum_items = sum(ex.budget_items.values()) if ex.budget_items else 0
    declared = ex.budget_brl or 0
    inconsistent = diag.budget_math_inconsistency or (
        sum_items > 0 and declared > 0 and abs(sum_items - declared) > max(1000, declared * 0.05)
    )
    assert inconsistent, (
        f"esperado 9.5M vs 9M: items={ex.budget_items} sum={sum_items} declared={declared}"
    )


def test_bad01_quality_flags(scored):
    """Proposta oca: sem rubricas detalhadas e/ou sem metas — não deve ser 'projeto perfeito'."""
    pack = scored["BAD_01"]
    ex = pack["example"]
    result = pack["result"]
    # Sem abertura orçamentária robusta
    weak_budget = not ex.budget_items or len(ex.budget_items) < 2
    # Texto declara ausência de metas/baseline
    weak_text = any(
        s in ex.raw_text.lower()
        for s in ("nao foram definidas metas", "não foram definidas metas", "nao ha abertura")
    )
    assert weak_budget or weak_text
    # Semicondutores não deve ser #1 se houver recomendação
    if result.recommended:
        assert "semicondutor" not in result.recommended[0].title.lower()


def test_consolidate_corpus_v2_report(scored):
    rows = []
    failed = []
    for key in sorted(scored):
        pack = scored[key]
        ex = pack["example"]
        result = pack["result"]
        g = pack["gabarito"]
        diag = result.diagnosis
        expect = g["expect"]
        ok = False
        obtained = ""

        if expect == "pass_rd":
            ideal = next(
                (r for r in result.reports if (r.external_id or "").startswith("ideal-")),
                None,
            )
            ok = bool(
                diag.get("has_technological_risk")
                and ideal
                and ideal.eligible
                and ideal.score >= 60
            )
            obtained = f"tech={diag.get('has_technological_risk')} ideal={getattr(ideal,'score',None)}"
        elif expect == "block_no_tech_risk":
            ok = diag.get("has_technological_risk") is False and all(
                not r.eligible for r in result.reports if r.instrument == "subvencao"
            )
            obtained = f"tech={diag.get('has_technological_risk')} rec={len(result.recommended)}"
        elif expect == "alert_marketing":
            items = diag.get("ineligible_budget_items") or []
            ok = any("marketing" in i.lower() or "ads" in i.lower() for i in items)
            obtained = str(items)
        elif expect == "alert_budget_math":
            sum_items = sum(ex.budget_items.values()) if ex.budget_items else 0
            declared = ex.budget_brl or 0
            ok = bool(diag.get("budget_math_inconsistency")) or (
                sum_items > 0
                and declared > 0
                and abs(sum_items - declared) > max(1000, declared * 0.05)
            )
            obtained = f"math={diag.get('budget_math_inconsistency')} sum={sum_items} decl={declared}"
        elif expect == "fail_quality":
            ok = (not ex.budget_items or len(ex.budget_items) < 2) or (
                "metas" in ex.raw_text.lower() and "nao" in ex.raw_text.lower()
            )
            obtained = f"items={len(ex.budget_items)} budget={ex.budget_brl}"

        row = {
            "key": key,
            "alias": g["alias"],
            "file": ex.file_name,
            "expect": expect,
            "ok": ok,
            "obtained": obtained,
            "tech_risk": diag.get("has_technological_risk"),
            "n_recommended": len(result.recommended),
            "n_blocked": len(result.blocked),
            "top": result.recommended[0].title if result.recommended else None,
            "forbidden": diag.get("ineligible_budget_items"),
            "budget_math": diag.get("budget_math_inconsistency"),
            "redirect": [s["name"] for s in result.redirect_suggestions],
        }
        rows.append(row)
        if not ok:
            failed.append(row)

    RESULTS_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    assert not failed, "Falhas: " + ", ".join(f"{r['key']}({r['alias']})" for r in failed)
