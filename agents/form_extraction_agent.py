"""Form Extraction Agent — heurística + Ollama para preencher formulário do projeto."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from app.llm import LLMClient, get_llm_client
from app.pdf_form import guess_form_fields, weak_fields

_SCHEMA_HINT: dict[str, Any] = {
    "title": "string|null",
    "summary": "string|null",
    "objectives": ["objetivo 1", "objetivo 2"],
    "methodology": "string|null",
    "expected_results": "string|null",
    "team": "string|null",
    "budget_brl": "string|null (ex: 2.400.000)",
    "duration_months": "number|null",
    "areas": ["agro", "visão computacional"],
    "counterpart": "string|null",
}

_MAX_TEXT_FOR_LLM = 12000


@dataclass
class FormExtractionResult:
    form: dict[str, Any]
    method: str
    weak_before: list[str]
    filled_by_llm: list[str]
    llm_notes: str = ""


def _clip_for_llm(text: str, max_chars: int = _MAX_TEXT_FOR_LLM) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-(max_chars // 2) :]
    return head + "\n\n[...texto omitido...]\n\n" + tail


def _merge_llm_into_form(
    form: dict[str, Any],
    llm_data: dict[str, Any],
    targets: list[str],
) -> list[str]:
    """Mescla só campos alvo ainda fracos; eleva confidence quando preenche."""
    filled: list[str] = []
    conf = dict(form.get("confidence") or {})
    evidence = dict(form.get("evidence") or {})

    for key in targets:
        if key not in llm_data:
            continue
        incoming = llm_data.get(key)
        if incoming is None or incoming == "" or incoming == []:
            continue

        if key == "objectives":
            if isinstance(incoming, str):
                objs = [ln.strip() for ln in incoming.splitlines() if ln.strip()]
            elif isinstance(incoming, list):
                objs = [str(x).strip() for x in incoming if str(x).strip()]
            else:
                continue
            if not objs:
                continue
            form["objectives"] = objs[:8]
            conf[key] = max(float(conf.get(key, 0) or 0), 0.72)
            evidence[key] = f"ollama:{objs[0][:160]}"
            filled.append(key)
            continue

        if key == "areas":
            if isinstance(incoming, str):
                areas = [a.strip() for a in re.split(r"[;|,]", incoming) if a.strip()]
            elif isinstance(incoming, list):
                areas = [str(a).strip() for a in incoming if str(a).strip()]
            else:
                continue
            if not areas:
                continue
            # Une com áreas heurísticas, sem duplicar.
            merged = list(form.get("areas") or [])
            for a in areas:
                if a not in merged:
                    merged.append(a)
            form["areas"] = merged[:10]
            conf[key] = max(float(conf.get(key, 0) or 0), 0.7)
            evidence[key] = f"ollama:{'; '.join(merged[:5])}"
            filled.append(key)
            continue

        if key == "duration_months":
            try:
                months = int(float(str(incoming).replace(",", ".").strip()))
            except (TypeError, ValueError):
                continue
            if not (1 <= months <= 120):
                continue
            form["duration_months"] = months
            conf[key] = max(float(conf.get(key, 0) or 0), 0.7)
            evidence[key] = f"ollama:{months} meses"
            filled.append(key)
            continue

        if key == "budget_brl":
            text = str(incoming).strip()
            text = text.replace("R$", "").strip()
            if len(text) < 3:
                continue
            form["budget_brl"] = text
            conf[key] = max(float(conf.get(key, 0) or 0), 0.7)
            evidence[key] = f"ollama:R$ {text}"
            filled.append(key)
            continue

        text = str(incoming).strip()
        if len(text) < 12 and key != "title":
            continue
        if key == "title" and len(text) < 8:
            continue
        form[key] = text[:2000] if key != "title" else text[:300]
        conf[key] = max(float(conf.get(key, 0) or 0), 0.72)
        evidence[key] = f"ollama:{text[:180]}"
        filled.append(key)

    form["confidence"] = conf
    form["evidence"] = evidence
    return filled


class FormExtractionAgent:
    """Pipeline: heurística → (opcional) Ollama só nos campos fracos."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm = llm or get_llm_client(self.settings)

    def extract(self, text: str, *, filename: str = "") -> FormExtractionResult:
        form = guess_form_fields(text, filename=filename)
        weak = weak_fields(form)
        filled: list[str] = []
        notes = "heuristic_only"

        use_llm = bool(self.settings.form_extract_use_llm)
        provider = (self.settings.llm_provider or "none").strip().lower()
        if use_llm and provider == "ollama" and weak and (text or "").strip():
            prompt = self._build_prompt(text=text, form=form, weak=weak)
            result = self.llm.extract_json(
                task="project_form_fields",
                prompt=prompt,
                schema_hint=_SCHEMA_HINT,
            )
            notes = result.notes
            if result.data and not result.used_fallback:
                filled = _merge_llm_into_form(form, result.data, weak)
                if filled:
                    form["extraction_method"] = "heuristic+ollama"
                    form["notes"] = (
                        "Campos preenchidos por heuristica + Ollama — revise antes de avaliar. "
                        f"LLM reforçou: {', '.join(filled)}."
                    )
                else:
                    form["extraction_method"] = "heuristic"
                    notes = notes + "; llm_sem_campos_uteis"
            else:
                form["extraction_method"] = "heuristic"
                notes = notes or "ollama_indisponivel"
        else:
            form["extraction_method"] = "heuristic"

        method = str(form.get("extraction_method") or "heuristic")
        return FormExtractionResult(
            form=form,
            method=method,
            weak_before=weak,
            filled_by_llm=filled,
            llm_notes=notes,
        )

    def _build_prompt(
        self,
        *,
        text: str,
        form: dict[str, Any],
        weak: list[str],
    ) -> str:
        partial = {k: form.get(k) for k in weak}
        return (
            "Extraia/complete APENAS estes campos fracos do formulario de projeto de fomento.\n"
            f"Campos alvo: {', '.join(weak)}\n"
            "Valores atuais (podem estar vazios ou ruins):\n"
            f"{partial}\n\n"
            "Texto do PDF (pode estar truncado):\n"
            f"{_clip_for_llm(text)}\n"
        )
