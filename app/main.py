"""Gateway FastAPI — health, orchestrator, Fase A UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agents.orchestrator import Orchestrator, PipelineRequest
from app.config import ROOT_DIR, get_settings
from app.routes_auth import router as auth_router
from app.routes_fase_a import router as fase_a_router
from app.schemas import SubmitProjectRequest, SubmitProjectResponse

settings = get_settings()
WEB_DIR = ROOT_DIR / "web"
LANDING_OUT = ROOT_DIR / "landing" / "out"

app = FastAPI(
    title=settings.app_name,
    version="0.4.0",
    description="Sistema de Agentes de IA para Gestao e Subvencao de Editais (TCC) — Fase A UI",
)

app.include_router(auth_router)
app.include_router(fase_a_router)

if WEB_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

_next_dir = LANDING_OUT / "_next"
if _next_dir.is_dir():
    app.mount("/_next", StaticFiles(directory=str(_next_dir)), name="landing_next")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "database_host": settings.database_host_hint,
        "llm_provider": settings.llm_provider,
        "llm_template_fallback": settings.llm_uses_template_fallback,
        "embedding_model": settings.embedding_model_name,
        "embedding_backend": settings.embedding_backend,
        "fase_a_ui": True,
        "landing": LANDING_OUT.joinpath("index.html").is_file(),
    }


@app.get("/")
def home_page() -> FileResponse:
    """Landing pública (Next export). Fallback: painel legado em web/index.html."""
    landing = LANDING_OUT / "index.html"
    if landing.is_file():
        return FileResponse(landing)
    path = WEB_DIR / "index.html"
    if not path.exists():
        raise HTTPException(404, "Landing nao encontrada (rode npm run build em landing/)")
    return FileResponse(path)


@app.get("/sads-logo.png")
def landing_logo() -> FileResponse:
    for candidate in (
        LANDING_OUT / "sads-logo.png",
        WEB_DIR / "assets" / "sads-logo.png",
    ):
        if candidate.is_file():
            return FileResponse(candidate)
    raise HTTPException(404, "Logo nao encontrado")


@app.get("/{page_name}.html")
def html_page(page_name: str) -> FileResponse:
    safe = Path(page_name).name
    path = WEB_DIR / f"{safe}.html"
    if not path.exists():
        raise HTTPException(404, f"Pagina nao encontrada: {safe}.html")
    return FileResponse(path)


@app.post("/api/v1/submit-project", response_model=SubmitProjectResponse)
async def submit_project(body: SubmitProjectRequest) -> SubmitProjectResponse:
    """Atalho legado: pipeline retrieve → score → generate → relatorio."""
    try:
        orch = Orchestrator()
        result = await orch.run(
            PipelineRequest(
                project_title=body.project_title,
                project_text=body.project_text,
                company_name=body.company_name,
                company_size=body.company_size,
                company_trl=body.company_trl,
                company_areas=body.company_areas,
                agency=body.agency,
                k=body.k,
                top_n_drafts=body.top_n_drafts,
            )
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Falha no pipeline: {exc}") from exc

    reports = (result.scoring or {}).get("reports") or []
    top = reports[0] if reports else None
    return SubmitProjectResponse(
        status="ok",
        created_at=result.created_at,
        report_path=result.report_path,
        top_score=(top or {}).get("score"),
        top_edict=(top or {}).get("external_id"),
        drafts_count=len(result.drafts),
        result=result.to_dict(),
    )
