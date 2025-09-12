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

# Permite definir o remetente via variáveis específicas ou valores antigos
DEFAULT_FROM = (
    os.getenv("NOTIFY_FROM_EMAIL")
    or os.getenv("MAIL_FROM")
    or os.getenv("RESEND_FROM", "no-reply@example.com")
)
DEFAULT_REPLY_TO = (
    os.getenv("NOTIFY_REPLY_TO") or os.getenv("RESEND_REPLY_TO")
)

Address = Union[str, Iterable[str]]

PLATAFORMA_URL = "https://mg.ead.senai.br/"
SENHA_INICIAL = "123456"


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

    if not RESEND_API_KEY:
        # Em ambientes sem API key, apenas registra o envio para fins de debug
        log.info(
            "EMAIL_SEND_SKIPPED",
            extra={"reason": "missing_api_key", "params": params},
        )
        return {"status": "logged", **params}

    result = resend.Emails.send(params)
    log.info(
        "EMAIL_SEND_SUCCESS",
        extra={"email_id": result.get("id"), "subject": subject},
    )
    return result


def render_email_template(name: str, **ctx: Any) -> str:
    template = current_app.jinja_env.get_or_select_template(f"email/{name}")
    return template.render(**ctx)


def enviar_notificacao_planejamento(
    assunto: str, nome_template: str, contexto: Dict[str, Any]
) -> None:
    """Envia notificações de planejamento para todos os e-mails cadastrados."""
    from src.models import EmailSecretaria  # import lazy to evitar ciclo

    try:
        emails = EmailSecretaria.query.all()
    except Exception as exc:  # pragma: no cover - log e retorna
        log.error(f"Erro ao buscar e-mails da secretaria: {exc}")
        return

    try:
        template = current_app.jinja_env.get_or_select_template(nome_template)
        html = template.render(**contexto)
    except Exception as exc:
        log.error(f"Erro ao renderizar template de e-mail {nome_template}: {exc}")
        return

    for registro in emails:
        destinatario = getattr(registro, "email", None)
        if not destinatario:
            continue
        try:
            send_email(to=destinatario, subject=assunto, html=html)
            log.info(
                "EMAIL_PLANEJAMENTO_NOTIFICACAO_SUCESSO",
                extra={"destinatario": destinatario, "assunto": assunto},
            )
        except Exception as exc:  # pragma: no cover - apenas log
            log.error(
                f"Falha ao enviar notificação de planejamento para {destinatario}: {exc}"
            )


def _build_convocacao_context(
    turma: Any, treinamento: Any, inscricao: Any
) -> Dict[str, Any]:
    return {
        "teoria_online": bool(getattr(turma, "teoria_online", False)),
        "tem_pratica": bool(getattr(treinamento, "tem_pratica", False)),
        "local_realizacao": getattr(turma, "local_realizacao", "-") or "-",
        "usuario_login": getattr(inscricao, "email", ""),
        "senha_inicial": SENHA_INICIAL,
        "plataforma_url": PLATAFORMA_URL,
    }


def enviar_convocacao(inscricao: Any, turma: Any) -> None:
    """Envia e-mail de convocação para um inscrito."""
    treinamento = getattr(turma, "treinamento", None)
    if treinamento is None:
        raise ValueError("Turma sem treinamento associado")

    fmt = "%d/%m/%Y"
    data_inicio = (
        turma.data_inicio.strftime(fmt)
        if getattr(turma, "data_inicio", None)
        else "-"
    )
    data_fim = (
        turma.data_fim.strftime(fmt)
        if getattr(turma, "data_fim", None)
        else None
    )

    ctx_extra = _build_convocacao_context(turma, treinamento, inscricao)
    destinatario = getattr(inscricao, "email", "")
    log.info(f"Tentando enviar e-mail de convocação para {destinatario}")

    html = render_email_template(
        "convocacao.html.j2",
        nome_inscrito=getattr(inscricao, "nome", ""),
        nome_treinamento=getattr(treinamento, "nome", ""),
        data_inicio=data_inicio,
        data_fim=data_fim,
        horario=getattr(turma, "horario", "-") or "-",
        carga_horaria=getattr(turma, "carga_horaria", None)
        or getattr(treinamento, "carga_horaria", None)
        or "-",
        instrutor=(
            getattr(
                getattr(turma, "instrutor", None),
                "nome",
                "-",
            )
            or "-"
        ),
        **ctx_extra,
    )

    subject = f"Convocação: {getattr(treinamento, 'nome', '')} — {data_inicio}"
    send_email(to=destinatario, subject=subject, html=html)
    log.info(f"E-mail de convocação enviado com sucesso para {destinatario}")
