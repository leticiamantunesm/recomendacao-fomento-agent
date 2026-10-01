"""Rotas Fase A — empresas, funcionarios, projetos, docs, applications, dashboard."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select

from agents.retrieval_agent import CompanyProfile, ProjectQuery, RetrievalAgent
from agents.scoring_agent import ScoringAgent
from app.cnpj_lookup import lookup_cnpj
from app.config import ROOT_DIR, get_settings
from app.pdf_form import guess_form_fields
from app.schemas import (
    ApplicationOut,
    ApplicationPatch,
    CnpjLookupOut,
    CompanyCreate,
    CompanyOut,
    DashboardOut,
    DocumentOut,
    DocumentPatch,
    EmployeeCreate,
    EmployeeOut,
    EvaluateRequest,
    ProjectOut,
    ProjectPatch,
)
from db.models import Application, Company, Document, Employee, Edict, Project
from db.session import session_scope
from scripts.extract_pdfs import extract_pdf, slugify

router = APIRouter(prefix="/api/v1")
settings = get_settings()


def _optional_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "undefined"}:
        return None
    return UUID(text)


def _safe_relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT_DIR.resolve()))
    except ValueError:
        return str(path)


def _unlink_if_upload(rel: str | None) -> None:
    if not rel:
        return
    path = (ROOT_DIR / rel).resolve()
    uploads_root = (settings.data_dir / "uploads").resolve()
    try:
        if uploads_root in path.parents or path.parent == uploads_root:
            if path.is_file():
                path.unlink()
    except OSError:
        pass


def _company_to_out(c: Company) -> CompanyOut:
    return CompanyOut.model_validate(c)


def _project_to_out(p: Project) -> ProjectOut:
    preview = (p.raw_text or "")[:500] or None
    return ProjectOut(
        id=p.id,
        company_id=p.company_id,
        created_by=p.created_by,
        title=p.title,
        status=p.status,
        file_path=p.file_path,
        form_data=p.form_data or {},
        raw_text_preview=preview,
        created_at=p.created_at,
    )


_FINEP_PAGE = "https://www.finep.gov.br/e/chamada-publica/222684"


def _finep_fallback_url(external_id: str | None) -> str | None:
    if not external_id:
        return None
    match = re.match(r"finep-(\d+)$", str(external_id).strip(), re.IGNORECASE)
    if not match:
        return None
    return f"{_FINEP_PAGE}/{match.group(1)}"


def _resolve_edict_url(
    *,
    breakdown: dict[str, Any] | None = None,
    report_url: str | None = None,
    edict_url: str | None = None,
    external_id: str | None = None,
) -> str | None:
    bd = breakdown or {}
    for candidate in (
        report_url,
        bd.get("edict_url"),
        bd.get("url"),
        edict_url,
        _finep_fallback_url(external_id),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _application_to_out(a: Application, edict_url: str | None = None) -> ApplicationOut:
    out = ApplicationOut.model_validate(a)
    out.url = _resolve_edict_url(
        breakdown=a.breakdown if isinstance(a.breakdown, dict) else {},
        edict_url=edict_url,
        external_id=a.edict_external_id,
    )
    return out


async def _edict_url_map(session, apps: list[Application]) -> dict[UUID, str | None]:
    edict_ids = [a.edict_id for a in apps if a.edict_id]
    if not edict_ids:
        return {}
    edict_rows = (await session.scalars(select(Edict).where(Edict.id.in_(edict_ids)))).all()
    return {e.id: e.url for e in edict_rows}


# ----- companies -----


@router.get("/cnpj/{cnpj}", response_model=CnpjLookupOut)
async def get_cnpj_lookup(cnpj: str) -> CnpjLookupOut:
    """Consulta base publica (BrasilAPI) e sugere porte + dados cadastrais."""
    try:
        data = await lookup_cnpj(cnpj)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Falha na consulta de CNPJ: {exc}") from exc
    return CnpjLookupOut.model_validate(data)


@router.post("/companies", response_model=CompanyOut)
async def create_company(body: CompanyCreate) -> CompanyOut:
    async with session_scope() as session:
        company = Company(
            name=body.name,
            trade_name=body.trade_name,
            cnpj=body.cnpj,
            size=body.size,
            employee_count=body.employee_count,
            revenue_brl=body.revenue_brl,
            uf=body.uf,
            city=body.city,
            cnae=body.cnae,
            areas=body.areas or [],
            email=body.email,
            phone=body.phone,
        )
        session.add(company)
        await session.commit()
        await session.refresh(company)
        return _company_to_out(company)


@router.get("/companies", response_model=list[CompanyOut])
async def list_companies() -> list[CompanyOut]:
    async with session_scope() as session:
        rows = (await session.scalars(select(Company).order_by(Company.created_at.desc()))).all()
        return [_company_to_out(c) for c in rows]


@router.get("/companies/{company_id}", response_model=CompanyOut)
async def get_company(company_id: UUID) -> CompanyOut:
    async with session_scope() as session:
        company = await session.get(Company, company_id)
        if not company:
            raise HTTPException(404, "Empresa nao encontrada")
        return _company_to_out(company)


@router.patch("/companies/{company_id}", response_model=CompanyOut)
async def patch_company(company_id: UUID, body: CompanyCreate) -> CompanyOut:
    async with session_scope() as session:
        company = await session.get(Company, company_id)
        if not company:
            raise HTTPException(404, "Empresa nao encontrada")
        for field, value in body.model_dump().items():
            setattr(company, field, value)
        await session.commit()
        await session.refresh(company)
        return _company_to_out(company)


# ----- employees -----


@router.post("/employees", response_model=EmployeeOut)
async def create_employee(body: EmployeeCreate) -> EmployeeOut:
    async with session_scope() as session:
        company = await session.get(Company, body.company_id)
        if not company:
            raise HTTPException(404, "Empresa nao encontrada")
        from app.auth import hash_password

        emp = Employee(
            company_id=body.company_id,
            name=body.name,
            email=body.email.strip().lower(),
            area=body.area,
            role_title=body.role_title,
            phone=body.phone,
            notes=body.notes,
            role=(body.role or "analyst").strip() or "analyst",
            password_hash=hash_password(body.password) if body.password else None,
            is_active=True,
        )
        session.add(emp)
        try:
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            raise HTTPException(400, f"Nao foi possivel criar funcionario: {exc}") from exc
        await session.refresh(emp)
        return _employee_to_out(emp)


def _employee_to_out(emp: Employee) -> EmployeeOut:
    return EmployeeOut(
        id=emp.id,
        company_id=emp.company_id,
        name=emp.name,
        email=emp.email,
        area=emp.area,
        role_title=emp.role_title,
        phone=emp.phone,
        notes=emp.notes,
        role=getattr(emp, "role", None) or "admin",
        is_active=bool(getattr(emp, "is_active", True)),
        created_at=emp.created_at,
        has_password=bool(getattr(emp, "password_hash", None)),
    )


@router.get("/employees", response_model=list[EmployeeOut])
async def list_employees(company_id: UUID) -> list[EmployeeOut]:
    async with session_scope() as session:
        rows = (
            await session.scalars(
                select(Employee)
                .where(Employee.company_id == company_id)
                .order_by(Employee.created_at.desc())
            )
        ).all()
        return [_employee_to_out(e) for e in rows]


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: UUID) -> EmployeeOut:
    async with session_scope() as session:
        emp = await session.get(Employee, employee_id)
        if not emp:
            raise HTTPException(404, "Funcionario nao encontrado")
        return _employee_to_out(emp)


# ----- projects -----


@router.post("/projects", response_model=ProjectOut)
async def create_project(
    company_id: str = Form(...),
    employee_id: str | None = Form(default=None),
    title: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> ProjectOut:
    try:
        company_uuid = _optional_uuid(company_id)
        if company_uuid is None:
            raise ValueError("company_id invalido")
        employee_uuid = _optional_uuid(employee_id)
    except ValueError as exc:
        raise HTTPException(400, f"Identificador invalido: {exc}") from exc

    filename = file.filename or "projeto.pdf"
    if not filename.lower().endswith(".pdf"):
        # aceita content-type PDF mesmo sem extensao
        if "pdf" not in (file.content_type or "").lower():
            raise HTTPException(400, "Envie um PDF (.pdf)")

    uploads = settings.data_dir / "uploads" / str(company_uuid)
    uploads.mkdir(parents=True, exist_ok=True)
    safe_stem = slugify(filename) or "projeto"
    safe_name = f"{uuid.uuid4().hex[:8]}_{safe_stem}.pdf"
    dest = uploads / safe_name

    try:
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Falha ao salvar PDF: {exc}") from exc

    try:
        raw_text, _pages, n_chars = extract_pdf(dest)
    except Exception as exc:  # noqa: BLE001
        raw_text, n_chars = "", 0
        form = guess_form_fields("", filename=filename)
        form["notes"] = f"Falha na extracao do PDF ({exc}). Preencha manualmente."
    else:
        form = guess_form_fields(raw_text, filename=filename)
        form["extracted_chars"] = n_chars

    if title and title.strip():
        form["title"] = title.strip()

    rel_path = _safe_relpath(dest)

    async with session_scope() as session:
        company = await session.get(Company, company_uuid)
        if not company:
            raise HTTPException(404, "Empresa nao encontrada")
        if employee_uuid:
            emp = await session.get(Employee, employee_uuid)
            if not emp or emp.company_id != company_uuid:
                raise HTTPException(400, "Funcionario invalido para a empresa")

        project = Project(
            company_id=company_uuid,
            created_by=employee_uuid,
            title=str(form.get("title") or filename)[:300],
            file_path=rel_path,
            raw_text=raw_text or None,
            status="draft",
            form_data=form,
            metadata_={"source_filename": filename, "extracted_chars": form.get("extracted_chars")},
        )
        session.add(project)
        await session.flush()

        doc = Document(
            company_id=company_uuid,
            project_id=project.id,
            filename=filename,
            file_path=rel_path,
            doc_type="project_pdf",
            content_type=file.content_type or "application/pdf",
            byte_size=dest.stat().st_size,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(project)
        return _project_to_out(project)


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(company_id: UUID) -> list[ProjectOut]:
    async with session_scope() as session:
        rows = (
            await session.scalars(
                select(Project)
                .where(Project.company_id == company_id)
                .order_by(Project.created_at.desc())
            )
        ).all()
        return [_project_to_out(p) for p in rows]


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: UUID) -> ProjectOut:
    async with session_scope() as session:
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(404, "Projeto nao encontrado")
        return _project_to_out(project)


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def patch_project(project_id: UUID, body: ProjectPatch) -> ProjectOut:
    async with session_scope() as session:
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(404, "Projeto nao encontrado")
        if body.title is not None:
            project.title = body.title
            fd = dict(project.form_data or {})
            fd["title"] = body.title
            project.form_data = fd
        if body.form_data is not None:
            merged = dict(project.form_data or {})
            merged.update(body.form_data)
            project.form_data = merged
            if "title" in body.form_data and body.form_data["title"]:
                project.title = str(body.form_data["title"])
        if body.status is not None:
            project.status = body.status
        await session.commit()
        await session.refresh(project)
        return _project_to_out(project)


@router.post("/projects/{project_id}/evaluate")
async def evaluate_project(project_id: UUID, body: EvaluateRequest | None = None) -> dict[str, Any]:
    body = body or EvaluateRequest()
    async with session_scope() as session:
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(404, "Projeto nao encontrado")
        if not project.company_id:
            raise HTTPException(400, "Projeto sem empresa")
        company = await session.get(Company, project.company_id)
        if not company:
            raise HTTPException(404, "Empresa nao encontrada")

        form = project.form_data or {}
        areas = list(company.areas or [])
        if isinstance(form.get("areas"), list):
            areas = list({*areas, *[str(a) for a in form["areas"]]})
        project_text = project.raw_text or str(form.get("summary") or project.title)
        if len(project_text) < 50:
            project_text = (project_text + "\n" + json.dumps(form, ensure_ascii=False))[:4000]

        form_trl = form.get("trl")
        project_trl = None
        if form_trl is not None and str(form_trl).strip().isdigit():
            project_trl = int(form_trl)
        elif company.trl is not None:
            project_trl = int(company.trl)

        company_profile = CompanyProfile(
            name=company.name,
            size=company.size,
            trl=project_trl,
            areas=areas,
            uf=company.uf,
        )
        project_query = ProjectQuery(
            title=project.title,
            text=project_text,
            budget_brl=form.get("budget_brl"),
        )

        # dados para fora da sessao
        company_id = company.id
        company_dump = {
            "name": company.name,
            "size": company.size,
            "trl": project_trl,
            "areas": areas,
            "uf": company.uf,
        }

    retrieval = RetrievalAgent()
    scoring = ScoringAgent()
    try:
        retrieval_result = await retrieval.retrieve(
            project_query,
            company_profile,
            k=body.k,
            agency=body.agency,
        )
        scoring_result = scoring.score_matches(
            project=project_query,
            company=company_profile,
            matches=retrieval_result.matches,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Falha na avaliacao: {exc}") from exc

    top_reports = scoring_result.reports[: body.top_n]
    saved: list[ApplicationOut] = []

    async with session_scope() as session:
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(404, "Projeto nao encontrado")

        # remove recomendacoes antigas deste projeto
        old = (
            await session.scalars(
                select(Application).where(
                    Application.project_id == project_id,
                    Application.status.in_(["recommended", "draft"]),
                )
            )
        ).all()
        for row in old:
            await session.delete(row)

        for i, report in enumerate(top_reports, start=1):
            edict_uuid = None
            edict_page_url: str | None = None
            if report.external_id:
                edict = await session.scalar(
                    select(Edict).where(Edict.external_id == report.external_id)
                )
                if edict:
                    edict_uuid = edict.id
                    edict_page_url = edict.url
            breakdown = report.breakdown.to_dict()
            page_url = _resolve_edict_url(
                breakdown=breakdown,
                report_url=getattr(report, "url", None),
                edict_url=edict_page_url,
                external_id=report.external_id,
            )
            if page_url:
                breakdown["edict_url"] = page_url
            app_row = Application(
                project_id=project_id,
                company_id=company_id,
                edict_id=edict_uuid,
                edict_external_id=report.external_id,
                edict_title=report.title,
                rank_position=i,
                score=report.score,
                breakdown=breakdown,
                strengths=report.strengths,
                weaknesses=report.weaknesses,
                summary=report.summary,
                status="recommended",
                was_in_top3=True,
            )
            session.add(app_row)

        project.status = "evaluated"
        await session.commit()

        apps = (
            await session.scalars(
                select(Application)
                .where(Application.project_id == project_id)
                .order_by(Application.rank_position.asc().nulls_last())
            )
        ).all()
        url_by_edict = await _edict_url_map(session, list(apps))
        saved = [
            _application_to_out(a, edict_url=url_by_edict.get(a.edict_id) if a.edict_id else None)
            for a in apps
        ]
        project_snap = {
            "id": str(project.id),
            "title": project.title,
            "status": project.status,
            "form_data": project.form_data or {},
            "raw_text_preview": (project.raw_text or "")[:500] or None,
            "file_path": project.file_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
        }

    return {
        "status": "ok",
        "project_id": str(project_id),
        "project": project_snap,
        "company": company_dump,
        "retrieval": retrieval_result.to_dict(),
        "applications": [a.model_dump(mode="json") for a in saved],
        "weights": (
            scoring_result.reports[0].breakdown.weights
            if scoring_result.reports
            else {}
        ),
    }


# ----- documents -----


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(company_id: UUID) -> list[DocumentOut]:
    async with session_scope() as session:
        rows = (
            await session.scalars(
                select(Document)
                .where(Document.company_id == company_id)
                .order_by(Document.created_at.desc())
            )
        ).all()
        return [DocumentOut.model_validate(d) for d in rows]


@router.post("/documents", response_model=DocumentOut)
async def upload_document(
    company_id: str = Form(...),
    project_id: str | None = Form(default=None),
    doc_type: str = Form(default="other"),
    file: UploadFile = File(...),
) -> DocumentOut:
    if not file.filename:
        raise HTTPException(400, "Arquivo obrigatorio")
    try:
        company_uuid = _optional_uuid(company_id)
        if company_uuid is None:
            raise ValueError("company_id invalido")
        project_uuid = _optional_uuid(project_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    uploads = settings.data_dir / "uploads" / str(company_uuid) / "materials"
    uploads.mkdir(parents=True, exist_ok=True)
    safe = f"{uuid.uuid4().hex[:8]}_{slugify(file.filename)}{Path(file.filename).suffix.lower() or '.bin'}"
    dest = uploads / safe
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    rel = _safe_relpath(dest)

    async with session_scope() as session:
        company = await session.get(Company, company_uuid)
        if not company:
            raise HTTPException(404, "Empresa nao encontrada")
        doc = Document(
            company_id=company_uuid,
            project_id=project_uuid,
            filename=file.filename,
            file_path=rel,
            doc_type=doc_type,
            content_type=file.content_type,
            byte_size=dest.stat().st_size,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return DocumentOut.model_validate(doc)


@router.patch("/documents/{document_id}", response_model=DocumentOut)
async def patch_document(document_id: UUID, body: DocumentPatch) -> DocumentOut:
    async with session_scope() as session:
        doc = await session.get(Document, document_id)
        if not doc:
            raise HTTPException(404, "Documento nao encontrado")
        if body.filename is not None:
            doc.filename = body.filename.strip()
        if body.doc_type is not None:
            doc.doc_type = body.doc_type.strip() or doc.doc_type
        await session.commit()
        await session.refresh(doc)
        return DocumentOut.model_validate(doc)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: UUID) -> dict[str, Any]:
    """Exclui material. Se for PDF de projeto, remove tambem o projeto e anexos ligados."""
    paths_to_unlink: list[str] = []
    removed_project_id: str | None = None

    async with session_scope() as session:
        doc = await session.get(Document, document_id)
        if not doc:
            raise HTTPException(404, "Documento nao encontrado")

        project_id = doc.project_id

        # PDF principal do projeto (criado em "Novo projeto"): apaga projeto + docs ligados
        if project_id and (doc.doc_type or "") == "project_pdf":
            siblings = (
                await session.scalars(select(Document).where(Document.project_id == project_id))
            ).all()
            for sibling in siblings:
                if sibling.file_path:
                    paths_to_unlink.append(sibling.file_path)
                await session.delete(sibling)

            project = await session.get(Project, project_id)
            if project:
                # applications sobem com ON DELETE CASCADE
                await session.delete(project)
                removed_project_id = str(project_id)
        else:
            if doc.file_path:
                paths_to_unlink.append(doc.file_path)
            await session.delete(doc)

            # se era o ultimo documento de um projeto orfao, limpa o projeto
            if project_id:
                remaining = int(
                    await session.scalar(
                        select(func.count())
                        .select_from(Document)
                        .where(Document.project_id == project_id)
                    )
                    or 0
                )
                if remaining == 0:
                    project = await session.get(Project, project_id)
                    if project:
                        await session.delete(project)
                        removed_project_id = str(project_id)

        await session.commit()

    for rel in paths_to_unlink:
        _unlink_if_upload(rel)

    return {
        "status": "deleted",
        "id": str(document_id),
        "project_deleted": removed_project_id,
    }


@router.delete("/projects/{project_id}")
async def delete_project(project_id: UUID) -> dict[str, Any]:
    """Exclui projeto, aplicacoes e documentos vinculados."""
    paths_to_unlink: list[str] = []
    async with session_scope() as session:
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(404, "Projeto nao encontrado")
        docs = (
            await session.scalars(select(Document).where(Document.project_id == project_id))
        ).all()
        for doc in docs:
            if doc.file_path:
                paths_to_unlink.append(doc.file_path)
            await session.delete(doc)
        await session.delete(project)
        await session.commit()
    for rel in paths_to_unlink:
        _unlink_if_upload(rel)
    return {"status": "deleted", "id": str(project_id)}



# ----- applications -----


@router.get("/applications", response_model=list[ApplicationOut])
async def list_applications(
    company_id: UUID,
    project_id: UUID | None = None,
) -> list[ApplicationOut]:
    async with session_scope() as session:
        stmt = select(Application).where(Application.company_id == company_id)
        if project_id is not None:
            stmt = stmt.where(Application.project_id == project_id)
        rows = (
            await session.scalars(stmt.order_by(Application.rank_position.asc().nulls_last()))
        ).all()
        url_by_edict = await _edict_url_map(session, list(rows))
        return [
            _application_to_out(a, edict_url=url_by_edict.get(a.edict_id) if a.edict_id else None)
            for a in rows
        ]


@router.patch("/applications/{application_id}", response_model=ApplicationOut)
async def patch_application(application_id: UUID, body: ApplicationPatch) -> ApplicationOut:
    async with session_scope() as session:
        app_row = await session.get(Application, application_id)
        if not app_row:
            raise HTTPException(404, "Aplicacao nao encontrada")
        if body.status is not None:
            app_row.status = body.status
            if body.status == "approved" and app_row.rank_position is not None:
                app_row.was_in_top3 = app_row.rank_position <= 3
        if body.approved_amount_brl is not None:
            app_row.approved_amount_brl = body.approved_amount_brl
        if body.outcome_notes is not None:
            app_row.outcome_notes = body.outcome_notes
        if body.was_in_top3 is not None:
            app_row.was_in_top3 = body.was_in_top3
        app_row.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(app_row)
        edict_url = None
        if app_row.edict_id:
            edict = await session.get(Edict, app_row.edict_id)
            edict_url = edict.url if edict else None
        return _application_to_out(app_row, edict_url=edict_url)


# ----- dashboard -----


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(company_id: UUID) -> DashboardOut:
    async with session_scope() as session:
        company = await session.get(Company, company_id)
        if not company:
            raise HTTPException(404, "Empresa nao encontrada")

        # Limpa projetos sem nenhum documento (orfaos de exclusoes antigas)
        orphan_projects = (
            await session.scalars(
                select(Project).where(
                    Project.company_id == company_id,
                    ~Project.id.in_(
                        select(Document.project_id).where(
                            Document.project_id.is_not(None),
                            Document.company_id == company_id,
                        )
                    ),
                )
            )
        ).all()
        for orphan in orphan_projects:
            await session.delete(orphan)
        if orphan_projects:
            await session.commit()

        projects_count = int(
            await session.scalar(
                select(func.count()).select_from(Project).where(Project.company_id == company_id)
            )
            or 0
        )
        evaluated_count = int(
            await session.scalar(
                select(func.count())
                .select_from(Project)
                .where(Project.company_id == company_id, Project.status == "evaluated")
            )
            or 0
        )
        docs_count = int(
            await session.scalar(
                select(func.count()).select_from(Document).where(Document.company_id == company_id)
            )
            or 0
        )
        emp_count = int(
            await session.scalar(
                select(func.count()).select_from(Employee).where(Employee.company_id == company_id)
            )
            or 0
        )

        apps = (
            await session.scalars(select(Application).where(Application.company_id == company_id))
        ).all()
        by_status: dict[str, int] = {}
        approved = 0
        rejected = 0
        savings = 0.0
        top3_hits = 0
        top3_total = 0
        for a in apps:
            by_status[a.status] = by_status.get(a.status, 0) + 1
            if a.status == "approved":
                approved += 1
                if a.approved_amount_brl is not None:
                    savings += float(a.approved_amount_brl)
                top3_total += 1
                if a.was_in_top3:
                    top3_hits += 1
            elif a.status == "rejected":
                rejected += 1
                top3_total += 1
                # rejected still counts for accuracy if was_in_top3 set when they chose that edict

        hit_rate = (top3_hits / top3_total) if top3_total else None

        return DashboardOut(
            company_id=company.id,
            company_name=company.name,
            projects_count=projects_count,
            evaluated_count=evaluated_count,
            applications_by_status=by_status,
            approved_count=approved,
            rejected_count=rejected,
            top3_hit_rate=hit_rate,
            estimated_savings_brl=round(savings, 2),
            documents_count=docs_count,
            employees_count=emp_count,
        )
