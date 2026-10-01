"""Rotas de autenticacao: register, login, me."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.auth import (
    AuthUser,
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    find_company_by_login_name,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.mailer import send_email
from app.schemas import (
    AuthTokenOut,
    AuthUserOut,
    ForgotPasswordOut,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from db.models import Company, Employee
from db.session import session_scope

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _user_out(emp: Employee, company: Company) -> AuthUserOut:
    return AuthUserOut(
        employee_id=emp.id,
        company_id=company.id,
        email=emp.email,
        name=emp.name,
        role=emp.role or "admin",
        company_name=company.name,
    )


def _token_out(emp: Employee, company: Company) -> AuthTokenOut:
    token = create_access_token(
        employee_id=emp.id,
        company_id=company.id,
        email=emp.email,
    )
    return AuthTokenOut(access_token=token, user=_user_out(emp, company))


@router.post("/register", response_model=AuthTokenOut)
async def register(body: RegisterRequest) -> AuthTokenOut:
    """Cria empresa + usuario admin com senha (onboarding)."""
    async with session_scope() as session:
        existing_company = await find_company_by_login_name(session, body.company_name)
        if existing_company:
            raise HTTPException(
                409,
                "Ja existe uma empresa com este nome. Use Login ou escolha outro nome.",
            )

        email = body.admin_email
        company = Company(
            name=body.company_name.strip(),
            trade_name=body.trade_name,
            cnpj=body.cnpj,
            size=body.size,
            uf=body.uf,
            city=body.city,
            email=body.company_email or email,
            phone=body.company_phone,
            areas=body.areas or [],
        )
        session.add(company)
        await session.flush()

        emp = Employee(
            company_id=company.id,
            name=body.admin_name.strip(),
            email=email,
            password_hash=hash_password(body.password),
            role="admin",
            is_active=True,
            role_title="Administrador",
            last_login_at=datetime.now(timezone.utc),
        )
        session.add(emp)
        await session.commit()
        await session.refresh(emp)
        await session.refresh(company)
        return _token_out(emp, company)


@router.post("/login", response_model=AuthTokenOut)
async def login(body: LoginRequest) -> AuthTokenOut:
    async with session_scope() as session:
        company = await find_company_by_login_name(session, body.company_name)
        if not company:
            raise HTTPException(401, "Empresa, e-mail ou senha invalidos.")

        emp = await session.scalar(
            select(Employee).where(
                Employee.company_id == company.id,
                Employee.email == body.email,
            )
        )
        if not emp or not emp.is_active:
            raise HTTPException(401, "Empresa, e-mail ou senha invalidos.")
        if not emp.password_hash:
            raise HTTPException(
                401,
                "Este usuario ainda nao possui senha. Conclua o cadastro/onboarding ou redefina a senha.",
            )
        if not verify_password(body.password, emp.password_hash):
            raise HTTPException(401, "Empresa, e-mail ou senha invalidos.")

        emp.last_login_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(emp)
        return _token_out(emp, company)


@router.get("/me", response_model=AuthUserOut)
async def me(user: AuthUser = Depends(get_current_user)) -> AuthUserOut:
    return AuthUserOut(
        employee_id=user.employee_id,
        company_id=user.company_id,
        email=user.email,
        name=user.name,
        role=user.role,
        company_name=user.company_name,
    )


@router.post("/logout")
async def logout() -> dict:
    """Logout e client-side (descarta o token). Endpoint para simetria de API."""
    return {"status": "ok"}


@router.post("/forgot-password", response_model=ForgotPasswordOut)
async def forgot_password(body: ForgotPasswordRequest) -> ForgotPasswordOut:
    """Gera link de redefinicao e tenta enviar por e-mail.

    Sempre responde de forma generica se a conta nao existir (anti-enumeration),
    exceto em desenvolvimento sem SMTP, quando devolvemos o reset_url.
    """
    settings = get_settings()
    generic = ForgotPasswordOut(
        message=(
            "Se encontrarmos uma conta com esses dados, enviaremos um link de "
            "redefinicao. Verifique a caixa de entrada e o spam."
        ),
        email_sent=False,
        reset_url=None,
    )

    async with session_scope() as session:
        company = await find_company_by_login_name(session, body.company_name)
        if not company:
            return generic
        emp = await session.scalar(
            select(Employee).where(
                Employee.company_id == company.id,
                Employee.email == body.email,
                Employee.is_active.is_(True),
            )
        )
        if not emp:
            return generic

        token = create_password_reset_token(
            employee_id=emp.id,
            company_id=company.id,
            email=emp.email,
        )
        base = settings.app_public_url.rstrip("/")
        reset_url = f"{base}/reset-password.html?token={token}"
        minutes = settings.auth_reset_ttl_minutes
        text = (
            f"Ola, {emp.name}.\n\n"
            f"Recebemos um pedido para redefinir a senha da sua conta SADS "
            f"({company.name}).\n\n"
            f"Abra o link abaixo (valido por {minutes} minutos):\n{reset_url}\n\n"
            f"Se voce nao solicitou, ignore este e-mail.\n"
        )
        html = (
            f"<p>Ola, <strong>{emp.name}</strong>.</p>"
            f"<p>Recebemos um pedido para redefinir a senha da conta SADS "
            f"(<strong>{company.name}</strong>).</p>"
            f"<p><a href=\"{reset_url}\">Redefinir minha senha</a></p>"
            f"<p>O link expira em {minutes} minutos. Se voce nao solicitou, ignore.</p>"
        )
        sent = send_email(
            to=emp.email,
            subject="SADS — redefinicao de senha",
            text_body=text,
            html_body=html,
        )

        # Sem SMTP: devolve o link na resposta para nao travar o usuario em local/TCC.
        include_url = (not sent) or (settings.app_env.lower() == "development")
        return ForgotPasswordOut(
            message=(
                "Enviamos um link de redefinicao para o e-mail cadastrado."
                if sent
                else (
                    "SMTP nao configurado: use o link abaixo para redefinir a senha agora. "
                    "Em producao, configure SMTP_HOST/SMTP_FROM no .env."
                )
            ),
            email_sent=sent,
            reset_url=reset_url if include_url else None,
        )


@router.post("/reset-password", response_model=AuthTokenOut)
async def reset_password(body: ResetPasswordRequest) -> AuthTokenOut:
    payload = decode_password_reset_token(body.token)
    try:
        employee_id = UUID(payload["eid"])
        company_id = UUID(payload["cid"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, "Link de redefinicao invalido.") from exc

    async with session_scope() as session:
        emp = await session.get(Employee, employee_id)
        if not emp or not emp.is_active or emp.company_id != company_id:
            raise HTTPException(400, "Link de redefinicao invalido ou usuario inativo.")
        company = await session.get(Company, company_id)
        if not company:
            raise HTTPException(400, "Empresa nao encontrada.")

        emp.password_hash = hash_password(body.password)
        emp.last_login_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(emp)
        return _token_out(emp, company)
