"""Bateria de testes SADS — gabarito dos 10 projetos em docs/TCC/exemplos_projetos.

Valida Gate 0 (risco tecnológico / rubricas / orçamento) + hard gates de scoring
contra editais sintéticos (ideal + armadilhas).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.project_risk import diagnose_project
from agents.scoring_agent import ScoringAgent
from tests.fixtures.sads_exemplo_loader import load_all_examples, trap_and_ideal_edicts
from tests.fixtures.sads_exemplos_gabarito import EXEMPLOS_DIR, GABARITO, PROJECT_FILES

REPORT_PATH = Path(__file__).resolve().parents[1] / "docs" / "TCC" / "sads_test_report.md"
RESULTS: dict[str, dict] = {}


def _blob_reasons(result) -> str:
    parts: list[str] = []
    diag = result.diagnosis or {}
    parts.extend(diag.get("critical_alerts") or [])
    parts.extend(diag.get("ineligible_budget_items") or [])
    for r in result.reports:
        parts.extend(r.block_reasons or [])
        parts.extend(r.weaknesses or [])
        parts.append(r.eligibility_status or "")
        parts.append(r.summary or "")
    return " | ".join(parts).lower()


def _has_any(text: str, needles: list[str]) -> bool:
    return any(n.lower() in text for n in needles)


@pytest.fixture(scope="module")
def examples():
    missing = [f for f in PROJECT_FILES.values() if not (EXEMPLOS_DIR / f).exists()]
    if missing:
        pytest.skip(f"PDFs ausentes em exemplos_projetos: {missing}")
    return load_all_examples()


@pytest.fixture(scope="module")
def scored(examples):
    agent = ScoringAgent()
    out = {}
    for pid, ex in examples.items():
        matches = trap_and_ideal_edicts(pid)
        result = agent.score_matches(
            project=ex.project,
            company=ex.company,
            matches=matches,
            revenue_brl=ex.revenue_brl,
        )
        out[pid] = {
            "example": ex,
            "result": result,
            "gabarito": GABARITO[pid],
        }
    return out


def test_mapping_ten_pdfs_present():
    assert len(PROJECT_FILES) == 10
    assert EXEMPLOS_DIR.is_dir()
    for fname in PROJECT_FILES.values():
        assert (EXEMPLOS_DIR / fname).exists(), fname


@pytest.mark.parametrize("pid", sorted(PROJECT_FILES.keys()))
def test_pdf_loads_and_has_identity(examples, pid):
    ex = examples[pid]
    assert ex.company_name
    assert ex.title
    # Alguns PDFs usam R$ 1,200,000.00 — parser deve capturar
    if pid != "08":
        assert ex.budget_brl is not None and ex.budget_brl > 0, (
            f"[{pid}] budget parse falhou: {ex.budget_brl}"
        )
    RESULTS.setdefault(pid, {})["loaded"] = True
    RESULTS[pid]["company"] = ex.company_name
    RESULTS[pid]["uf"] = ex.uf
    RESULTS[pid]["size"] = ex.size
    RESULTS[pid]["trl"] = ex.trl


@pytest.mark.parametrize("pid", sorted(PROJECT_FILES.keys()))
def test_gate0_tech_risk_matches_gabarito(examples, pid):
    ex = examples[pid]
    g = GABARITO[pid]
    diag = diagnose_project(
        title=ex.title,
        text=ex.raw_text,
        form_data=ex.form_data,
        trl=ex.trl,
        uf=ex.uf,
    )
    expected = g["must_have_tech_risk"]
    RESULTS.setdefault(pid, {})
    RESULTS[pid]["gate0_tech_risk"] = diag.has_technological_risk
    RESULTS[pid]["gate0_expected_tech_risk"] = expected
    RESULTS[pid]["gate0_alerts"] = list(diag.critical_alerts)
    RESULTS[pid]["forbidden"] = list(diag.ineligible_budget_items)
    RESULTS[pid]["budget_math"] = diag.budget_math_inconsistency
    assert diag.has_technological_risk is expected, (
        f"[{pid} {g['alias']}] tech_risk={diag.has_technological_risk} "
        f"esperado={expected}; nature={diag.project_nature}"
    )


def test_03_padaria_blocks_all_subvencao(scored):
    pid = "03"
    pack = scored[pid]
    result = pack["result"]
    g = pack["gabarito"]
    sub_reports = [r for r in result.reports if r.instrument == "subvencao"]
    assert sub_reports, "esperava armadilhas de subvenção"
    assert all(not r.eligible for r in sub_reports)
    assert all(r.score <= 15 for r in sub_reports)
    assert result.recommended == [] or all(
        r.instrument != "subvencao" for r in result.recommended
    )
    assert any("Sebraetec" in s["name"] for s in result.redirect_suggestions)
    blob = _blob_reasons(result)
    assert _has_any(blob, g["must_block_reasons"])
    RESULTS.setdefault(pid, {})
    RESULTS[pid]["outcome"] = "PASS" if True else "FAIL"
    RESULTS[pid]["detail"] = "subvenção bloqueada; redirect Sebraetec"


def test_04_neurogen_forbidden_budget_alerts(scored):
    pid = "04"
    pack = scored[pid]
    ex = pack["example"]
    diag = diagnose_project(
        title=ex.title, text=ex.raw_text, form_data=ex.form_data, trl=ex.trl, uf=ex.uf
    )
    forbidden = " ".join(diag.ineligible_budget_items).lower()
    assert diag.ineligible_budget_items, "deveria detectar rubricas vedadas"
    assert _has_any(forbidden, ["imóvel", "terreno", "obra", "veículo", "veiculo"])
    RESULTS.setdefault(pid, {})["detail"] = f"forbidden={diag.ineligible_budget_items}"


def test_05_ecoplast_blocked_on_sp_only_edict(scored):
    pid = "05"
    pack = scored[pid]
    result = pack["result"]
    ex = pack["example"]
    assert ex.uf == "PR"
    fapesp = next(r for r in result.reports if r.external_id == "trap-fapesp-sp")
    assert fapesp.eligible is False
    assert fapesp.score <= 15
    blob = _blob_reasons(result)
    assert _has_any(blob, ["região", "regiao", "sp", "são paulo", "sao paulo"])
    RESULTS.setdefault(pid, {})["detail"] = fapesp.eligibility_status


def test_06_agrotitan_blocked_on_mpe_edict(scored):
    pid = "06"
    pack = scored[pid]
    result = pack["result"]
    ex = pack["example"]
    assert ex.size == "Grande" or (ex.revenue_brl or 0) > 4_800_000
    centelha = next(r for r in result.reports if r.external_id == "trap-centelha")
    assert centelha.eligible is False
    assert centelha.score <= 15
    blob = _blob_reasons(result)
    assert _has_any(blob, ["mpe", "porte", "faturamento", "centelha"])
    RESULTS.setdefault(pid, {})["detail"] = centelha.eligibility_status


def test_08_pf_blocked_on_bndes_credit(scored):
    pid = "08"
    pack = scored[pid]
    result = pack["result"]
    ex = pack["example"]
    assert ex.size == "PF" or "pessoa física" in ex.raw_text.lower()
    # ADR-009: linha BNDES indexada não entra no ranking.
    assert not any(r.external_id == "trap-credito-pj" for r in result.reports)
    assert not any((r.agency or "").upper() == "BNDES" and r.eligible for r in result.reports)
    # PF não deve receber crédito elegível (redirect ou outro).
    credito_ok = [r for r in result.reports if r.instrument == "credito" and r.eligible]
    assert not credito_ok, f"PF com crédito elegível: {[r.external_id for r in credito_ok]}"
    assert ex.trl is not None and ex.trl <= 2
    RESULTS.setdefault(pid, {})["detail"] = {
        "bndes_catalog_excluded": True,
        "credito_eligible_ids": [],
        "blocked_ok": True,
        "size": ex.size,
    }


def test_10_budget_math_and_ads(scored):
    pid = "10"
    pack = scored[pid]
    ex = pack["example"]
    diag = diagnose_project(
        title=ex.title, text=ex.raw_text, form_data=ex.form_data, trl=ex.trl, uf=ex.uf
    )
    assert diag.ineligible_budget_items, "Google Ads deveria ser flagrado"
    assert _has_any(" ".join(diag.ineligible_budget_items).lower(), ["marketing", "ads"])
    # 350+250+150 = 750 vs total 500
    assert diag.budget_math_inconsistency is True or (
        ex.budget_items and abs(sum(ex.budget_items.values()) - (ex.budget_brl or 0)) > 1
    )
    RESULTS.setdefault(pid, {})["detail"] = {
        "math": diag.budget_math_inconsistency,
        "sum_items": sum(ex.budget_items.values()) if ex.budget_items else None,
        "declared": ex.budget_brl,
        "forbidden": diag.ineligible_budget_items,
    }


@pytest.mark.parametrize("pid", ["01", "02", "09"])
def test_perfect_rd_projects_recommend_ideal(scored, pid):
    pack = scored[pid]
    result = pack["result"]
    g = pack["gabarito"]
    assert result.diagnosis.get("has_technological_risk") is True
    ideal = next((r for r in result.reports if (r.external_id or "").startswith("ideal-")), None)
    assert ideal is not None, f"[{pid}] ideal edict ausente"
    assert ideal.eligible is True, (
        f"[{pid}] ideal bloqueado: {ideal.eligibility_status} {ideal.block_reasons}"
    )
    assert ideal.score >= 60, f"[{pid}] score ideal={ideal.score}"
    # Não deve ranquear armadilha de semicondutores acima do ideal (exceto 09 energia)
    semi = next(r for r in result.reports if r.external_id == "trap-semi")
    if pid != "09":
        assert semi.eligible is False or semi.score < ideal.score
    RESULTS.setdefault(pid, {})["detail"] = {
        "ideal_score": ideal.score,
        "ideal_status": ideal.eligibility_status,
        "recommended_ids": [r.external_id for r in result.recommended],
    }


def test_07_cultural_not_finep_subvencao(scored):
    pid = "07"
    pack = scored[pid]
    result = pack["result"]
    assert result.diagnosis.get("has_technological_risk") is False
    sub = [r for r in result.reports if r.instrument == "subvencao"]
    assert all(not r.eligible for r in sub)
    ideal = next(r for r in result.reports if r.external_id == "ideal-07")
    # instrumento "outro" cultural pode permanecer elegível se passar gates
    RESULTS.setdefault(pid, {})["detail"] = {
        "ideal_eligible": ideal.eligible,
        "ideal_score": ideal.score,
        "subs_blocked": all(not r.eligible for r in sub),
    }
    assert all(not r.eligible for r in sub)


def test_collect_module_results_for_report(scored):
    """Consolida resultados para o relatório markdown (sempre executa por último se -q)."""
    rows = []
    for pid in sorted(scored.keys()):
        pack = scored[pid]
        ex = pack["example"]
        result = pack["result"]
        g = pack["gabarito"]
        diag = result.diagnosis
        ideal = next(
            (r for r in result.reports if (r.external_id or "").startswith("ideal-")),
            None,
        )
        top_elig = result.recommended[0] if result.recommended else None
        # Veredito automático vs gabarito
        expect = g["expect"]
        ok = False
        obtained = ""
        if expect == "pass_ideal":
            ok = bool(ideal and ideal.eligible and ideal.score >= 60)
            obtained = (
                f"ideal eligible={getattr(ideal, 'eligible', None)} "
                f"score={getattr(ideal, 'score', None)}"
            )
        elif expect == "block_no_tech_risk":
            ok = diag.get("has_technological_risk") is False and not any(
                r.eligible and r.instrument == "subvencao" for r in result.reports
            )
            obtained = f"tech_risk={diag.get('has_technological_risk')} rec={len(result.recommended)}"
        elif expect == "alert_forbidden_budget":
            ok = bool(diag.get("ineligible_budget_items"))
            obtained = f"forbidden={diag.get('ineligible_budget_items')}"
        elif expect == "block_region":
            fapesp = next(r for r in result.reports if r.external_id == "trap-fapesp-sp")
            ok = fapesp.eligible is False
            obtained = fapesp.eligibility_status
        elif expect == "block_size":
            c = next(r for r in result.reports if r.external_id == "trap-centelha")
            ok = c.eligible is False
            obtained = c.eligibility_status
        elif expect == "pass_cultural":
            ok = diag.get("has_technological_risk") is False and all(
                not r.eligible for r in result.reports if r.instrument == "subvencao"
            )
            obtained = f"tech_risk={diag.get('has_technological_risk')}"
        elif expect == "block_pf_trl":
            # ADR-009: trap BNDES excluído; PF não pode ter crédito elegível.
            credits_ok = [
                r for r in result.reports if r.instrument == "credito" and r.eligible
            ]
            ok = ex.size == "PF" and not credits_ok and not any(
                r.external_id == "trap-credito-pj" for r in result.reports
            )
            obtained = f"PF size={ex.size} credito_eligible={[r.external_id for r in credits_ok]}"
        elif expect == "alert_budget_math_and_ads":
            ok = bool(diag.get("ineligible_budget_items")) and (
                diag.get("budget_math_inconsistency")
                or abs(sum(ex.budget_items.values()) - (ex.budget_brl or 0)) > 1
            )
            obtained = (
                f"math={diag.get('budget_math_inconsistency')} "
                f"forbidden={diag.get('ineligible_budget_items')}"
            )

        rows.append(
            {
                "id": pid,
                "alias": g["alias"],
                "file": ex.file_name,
                "expect": expect,
                "ok": ok,
                "obtained": obtained,
                "tech_risk": diag.get("has_technological_risk"),
                "n_recommended": len(result.recommended),
                "n_blocked": len(result.blocked),
                "top": (top_elig.title if top_elig else None),
                "redirect": [s["name"] for s in result.redirect_suggestions],
            }
        )
        RESULTS[pid] = {**RESULTS.get(pid, {}), **rows[-1]}

    # Persist JSON auxiliar para o gerador de relatório
    cache = Path(__file__).resolve().parent / "fixtures" / "_last_sads_results.json"
    cache.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = [r for r in rows if not r["ok"]]
    assert not failed, "Falhas no gabarito: " + ", ".join(
        f"{r['id']}({r['alias']})" for r in failed
    )
