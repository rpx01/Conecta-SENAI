"""Serviços utilitários para envio de notificações do módulo de chamados."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, Optional

from flask import current_app, render_template

from src.services.email_service import send_email

log = logging.getLogger(__name__)


ALLOWED_STATES = {"1", "true", "on", "yes"}


def notifications_enabled() -> bool:
    """Retorna se o envio de e-mails de chamados está habilitado."""
    flag = os.getenv("SEND_TICKET_EMAILS", "1")
    return flag.lower() in ALLOWED_STATES


def send_ticket_email(
    subject: str,
    template: str,
    context: Dict[str, Any],
    to: Iterable[str] | str,
    text_template: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Envia um e-mail relacionado aos chamados de TI."""
    if not notifications_enabled():
        log.info("Ticket e-mail disabled; skipping send", extra={"template": template})
        return None

    html = render_template(f"emails/{template}", **context)
    text_body = None
    if text_template:
        text_body = render_template(f"emails/{text_template}", **context)

    try:
        response = send_email(
            to=to,
            subject=subject,
            html=html,
            text=text_body,
        )
        log.debug(
            "Ticket e-mail sent", extra={"template": template, "to": to, "response": response}
        )
        return response
    except Exception:  # pragma: no cover - loga e propaga
        log.exception("Erro ao enviar e-mail de chamado", extra={"template": template})
        if current_app and current_app.debug:
            raise
        return None
