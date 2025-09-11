from __future__ import annotations
import os
from typing import Iterable, Optional, Dict, Any, List, Union
import logging

import resend
from flask import current_app

log = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
# Permite definir o remetente tanto via MAIL_FROM quanto RESEND_FROM
DEFAULT_FROM = os.getenv("MAIL_FROM") or os.getenv("RESEND_FROM", "no-reply@example.com")
DEFAULT_REPLY_TO = os.getenv("RESEND_REPLY_TO")

Address = Union[str, Iterable[str]]


def _normalize(addr: Address | None) -> Optional[List[str]]:
    if addr is None:
        return None
    if isinstance(addr, str):
        return [addr]
    return list(addr)


def send_email(
    to: Address,
    subject: str,
    html: str,
    text: Optional[str] = None,
    cc: Address | None = None,
    bcc: Address | None = None,
    reply_to: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    tags: Optional[List[Dict[str, str]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    from_: Optional[str] = None,
) -> Dict[str, Any]:
    """Envia e-mail via Resend."""
    params = {
        "from": from_ or DEFAULT_FROM,
        "to": _normalize(to),
        "subject": subject,
        "html": html,
    }
    if text:
        params["text"] = text
    if cc:
        params["cc"] = _normalize(cc)
    if bcc:
        params["bcc"] = _normalize(bcc)
    if reply_to or DEFAULT_REPLY_TO:
        params["reply_to"] = reply_to or DEFAULT_REPLY_TO
    if headers:
        params["headers"] = headers
    if tags:
        params["tags"] = tags
    if attachments:
        params["attachments"] = attachments

    log.debug(
        "EMAIL_SEND_START", extra={"to": params["to"], "subject": subject}
    )
    result = resend.Emails.send(params)
    log.info(
        "EMAIL_SEND_SUCCESS",
        extra={"email_id": result.get("id"), "subject": subject},
    )
    return result


def render_email_template(name: str, **ctx: Any) -> str:
    template = current_app.jinja_env.get_or_select_template(f"email/{name}")
    return template.render(**ctx)
