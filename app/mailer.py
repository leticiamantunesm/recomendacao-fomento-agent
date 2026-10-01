"""Envio de e-mail (SMTP opcional). Sem SMTP, apenas loga o conteudo."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger("sads.mail")


def smtp_configured() -> bool:
    settings = get_settings()
    return bool(settings.smtp_host and settings.smtp_from)


def send_email(*, to: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """Envia e-mail. Retorna True se enviou via SMTP; False se so registrou em log."""
    settings = get_settings()
    if not smtp_configured():
        logger.warning(
            "SMTP nao configurado — e-mail NAO enviado.\nPara: %s\nAssunto: %s\n%s",
            to,
            subject,
            text_body,
        )
        print(f"\n=== EMAIL (dev, SMTP off) → {to} ===\n{subject}\n{text_body}\n=== fim ===\n")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user or "noreply@sads.local"
    msg["To"] = to
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host or "", settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
    return True
