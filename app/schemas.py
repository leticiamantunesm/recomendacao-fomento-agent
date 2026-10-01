"""Schemas Pydantic da API (submit-project + Fase A UI)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# --- legado orchestrator ---


class SubmitProjectRequest(BaseModel):
    project_title: str = Field(..., min_length=3, max_length=300)
    project_text: str = Field(..., min_length=50)
    company_name: str = "Empresa Demo TCC"
    company_size: str | None = "EPP"
    company_trl: int | None = Field(default=5, ge=1, le=9)
    company_areas: list[str] = Field(default_factory=lambda: ["inovacao", "tecnologias digitais"])
    agency: str | None = "FINEP"
    k: int = Field(default=5, ge=1, le=20)
    top_n_drafts: int = Field(default=1, ge=1, le=3)


class SubmitProjectResponse(BaseModel):
    status: str
    created_at: str
    report_path: str | None
    top_score: float | None = None
    top_edict: str | None = None
    drafts_count: int = 0
    result: dict


# --- Fase A ---


def _split_areas(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in re_split_areas(value) if p.strip()]


def re_split_areas(raw: str) -> list[str]:
    import re

    return re.split(r"[;|,]", raw)


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    trade_name: str | None = None
    cnpj: str | None = None
    size: str | None = "EPP"
    employee_count: int | None = Field(default=None, ge=0)
    revenue_brl: Decimal | None = None
    uf: str | None = None
    city: str | None = None
    cnae: str | None = None
    areas: list[str] = Field(default_factory=list)
    email: str | None = None
    phone: str | None = None

    @field_validator("areas", mode="before")
    @classmethod
    def _areas(cls, v):  # noqa: ANN001
        return _split_areas(v)


class CompanyOut(BaseModel):
    id: UUID
    name: str
    trade_name: str | None = None
    cnpj: str | None = None
    size: str | None = None
    employee_count: int | None = None
    revenue_brl: Decimal | None = None
    uf: str | None = None
    city: str | None = None
    cnae: str | None = None
    areas: list[str] = []
    email: str | None = None
    phone: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CnpjLookupOut(BaseModel):
    cnpj: str
    name: str | None = None
    trade_name: str | None = None
    size: str | None = None
    porte_raw: str | None = None
    uf: str | None = None
    city: str | None = None
    cnae: str | None = None
    email: str | None = None
    phone: str | None = None
    areas: list[str] = []
    capital_social: float | int | str | None = None
    situacao_cadastral: str | None = None
    source: str = "brasilapi"


class DocumentPatch(BaseModel):
    filename: str | None = Field(default=None, min_length=1, max_length=300)
    doc_type: str | None = None



class EmployeeCreate(BaseModel):
    company_id: UUID
    name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., min_length=5, max_length=200)
    area: str | None = None
    role_title: str | None = None
    phone: str | None = None
    notes: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: str | None = Field(default="analyst", max_length=40)


class EmployeeOut(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    email: str
    area: str | None = None
    role_title: str | None = None
    phone: str | None = None
    notes: str | None = None
    role: str | None = "admin"
    is_active: bool = True
    created_at: datetime | None = None
    has_password: bool = False

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    """Onboarding: cria empresa + primeiro usuario admin."""

    company_name: str = Field(..., min_length=2, max_length=300)
    trade_name: str | None = None
    cnpj: str | None = None
    size: str | None = "EPP"
    uf: str | None = None
    city: str | None = None
    company_email: str | None = None
    company_phone: str | None = None
    areas: list[str] = Field(default_factory=list)
    admin_name: str = Field(..., min_length=2, max_length=200)
    admin_email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("areas", mode="before")
    @classmethod
    def _reg_areas(cls, v):  # noqa: ANN001
        return _split_areas(v)

    @field_validator("admin_email", mode="before")
    @classmethod
    def _norm_email(cls, v):  # noqa: ANN001
        return str(v or "").strip().lower()


class LoginRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=300)
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def _login_email(cls, v):  # noqa: ANN001
        return str(v or "").strip().lower()


class AuthUserOut(BaseModel):
    employee_id: UUID
    company_id: UUID
    email: str
    name: str
    role: str
    company_name: str


class AuthTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserOut


class ForgotPasswordRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=300)
    email: str = Field(..., min_length=5, max_length=200)

    @field_validator("email", mode="before")
    @classmethod
    def _forgot_email(cls, v):  # noqa: ANN001
        return str(v or "").strip().lower()


class ForgotPasswordOut(BaseModel):
    status: str = "ok"
    message: str
    email_sent: bool = False
    # Em desenvolvimento (sem SMTP), devolvemos o link para o usuario conseguir recuperar.
    reset_url: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=20)
    password: str = Field(..., min_length=8, max_length=128)


class ProjectFormData(BaseModel):
    title: str | None = None
    summary: str | None = None
    objectives: list[str] | str | None = None
    methodology: str | None = None
    expected_results: str | None = None
    team: str | None = None
    budget_brl: str | None = None
    duration_months: int | None = None
    areas: list[str] | str | None = None
    counterpart: str | None = None
    notes: str | None = None


class ProjectOut(BaseModel):
    id: UUID
    company_id: UUID | None
    created_by: UUID | None = None
    title: str
    status: str
    file_path: str | None = None
    form_data: dict[str, Any] = {}
    raw_text_preview: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProjectPatch(BaseModel):
    title: str | None = None
    form_data: dict[str, Any] | None = None
    status: str | None = None


class EvaluateRequest(BaseModel):
    agency: str | None = "FINEP"
    k: int = Field(default=8, ge=1, le=20)
    top_n: int = Field(default=5, ge=1, le=10)


class ApplicationOut(BaseModel):
    id: UUID
    project_id: UUID
    company_id: UUID
    edict_id: UUID | None = None
    edict_external_id: str | None = None
    edict_title: str | None = None
    url: str | None = None
    rank_position: int | None = None
    score: float | None = None
    breakdown: dict[str, Any] = {}
    strengths: list[str] = []
    weaknesses: list[str] = []
    summary: str | None = None
    status: str
    approved_amount_brl: Decimal | None = None
    outcome_notes: str | None = None
    was_in_top3: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApplicationPatch(BaseModel):
    status: str | None = None
    approved_amount_brl: Decimal | None = None
    outcome_notes: str | None = None
    was_in_top3: bool | None = None


class DocumentOut(BaseModel):
    id: UUID
    company_id: UUID
    project_id: UUID | None = None
    filename: str
    file_path: str
    doc_type: str
    content_type: str | None = None
    byte_size: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    company_id: UUID
    company_name: str
    projects_count: int
    evaluated_count: int
    applications_by_status: dict[str, int]
    approved_count: int
    rejected_count: int
    top3_hit_rate: float | None
    estimated_savings_brl: float
    documents_count: int
    employees_count: int
