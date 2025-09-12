from __future__ import annotations
import os
import base64
from typing import Iterable, Optional, Dict, Any, List, Union
import logging
import re

import resend
from flask import current_app
from types import SimpleNamespace
from datetime import datetime, time

log = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
# Permite definir o remetente tanto via MAIL_FROM quanto RESEND_FROM
DEFAULT_FROM = os.getenv("MAIL_FROM") or os.getenv(
    "RESEND_FROM", "no-reply@example.com"
)
DEFAULT_REPLY_TO = os.getenv("RESEND_REPLY_TO")

Address = Union[str, Iterable[str]]

PLATAFORMA_URL = "https://mg.ead.senai.br/"
SENHA_INICIAL = "123456"


def _normalize(addr: Address | None) -> Optional[List[str]]:
    if addr is None:
        return None
    if isinstance(addr, str):
        return [addr]
    return list(addr)


def _parse_time(value: Any) -> time | None:
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        digits = [int(x) for x in re.findall(r"\d+", value)]
        if digits:
            hour = digits[0]
            minute = digits[1] if len(digits) > 1 else 0
            try:
                return time(hour, minute)
            except ValueError:
                return None
    return None


def build_turma_context(turma: Any) -> SimpleNamespace:
    treino = getattr(turma, "treinamento", None)
    return SimpleNamespace(
        treinamento=SimpleNamespace(nome=getattr(treino, "nome", "")),
        nome=getattr(turma, "nome", ""),
        instrutor=getattr(turma, "instrutor", None),
        data_inicio=getattr(turma, "data_inicio", None),
        data_termino=getattr(turma, "data_fim", None),
        horario_inicio=_parse_time(
            getattr(turma, "horario_inicio", getattr(turma, "horario", None))
        )
        or time(0, 0),
        horario_fim=_parse_time(
            getattr(turma, "horario_fim", getattr(turma, "horario", None))
        )
        or time(0, 0),
        local=getattr(turma, "local", getattr(turma, "local_realizacao", "")),
        capacidade_maxima=getattr(turma, "capacidade_maxima", None),
    )


def build_user_context(nome: str) -> SimpleNamespace:
    return SimpleNamespace(name=nome)


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
    attachments = list(attachments) if attachments else []
    logo_path = None
    try:
        logo_path = os.path.join(
            current_app.static_folder, "img", "Logo-assinatura do e-mail.png"
        )
    except RuntimeError:
        logo_path = None

    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        attachments.append(
            {
                "filename": "logo_assinatura.png",
                "content": encoded,
                "content_id": "logo_assinatura",
            }
        )
    else:
        try:
            current_app.logger.warning(
                f"Logo de assinatura não encontrado em: {logo_path}"
            )
        except RuntimeError:
            pass

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

    ctx_extra = _build_convocacao_context(turma, treinamento, inscricao)
    destinatario = getattr(inscricao, "email", "")
    log.info(f"Tentando enviar e-mail de convocação para {destinatario}")

    turma_ctx = build_turma_context(turma)
    user_ctx = build_user_context(getattr(inscricao, "nome", ""))
    html = render_email_template(
        "convocacao.html.j2",
        user=user_ctx,
        turma=turma_ctx,
        **ctx_extra,
    )

    subject = f"Convocação: {getattr(treinamento, 'nome', '')} — {turma_ctx.data_inicio.strftime('%d/%m/%Y') if turma_ctx.data_inicio else ''}"
    send_email(to=destinatario, subject=subject, html=html)
    log.info(f"E-mail de convocação enviado com sucesso para {destinatario}")

def listar_emails_secretaria() -> List[str]:
    """Retorna todos os e-mails cadastrados para a secretaria de treinamentos."""
    from src.models.secretaria_treinamentos import SecretariaTreinamentos  # lazy import

    registros = SecretariaTreinamentos.query.all()
    return [r.email for r in registros if getattr(r, "email", None)]


def notificar_nova_turma(turma: "TurmaTreinamento") -> None:
    """Notifica instrutor e secretaria sobre criação de nova turma."""
    treinamento = getattr(turma, "treinamento", None)
    if not treinamento:
        return

    fmt = "%d/%m/%Y"
    data_inicio = turma.data_inicio.strftime(fmt) if getattr(turma, "data_inicio", None) else ""
    data_fim = turma.data_fim.strftime(fmt) if getattr(turma, "data_fim", None) else None
    ctx = {
        "treinamento_nome": getattr(treinamento, "nome", ""),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "horario": getattr(turma, "horario", "-") or "-",
        "local_realizacao": getattr(turma, "local_realizacao", "-") or "-",
    }

    instrutor = getattr(turma, "instrutor", None)
    if instrutor and getattr(instrutor, "email", None):
        html = render_email_template(
            "nova_turma_instrutor.html.j2", **ctx, instrutor_nome=instrutor.nome
        )
        subject = f"Nova turma designada - {ctx['treinamento_nome']}"
        send_email(instrutor.email, subject, html)

    emails_secretaria = listar_emails_secretaria()
    if emails_secretaria:
        turma_ctx = build_turma_context(turma)
        html_sec = render_email_template(
            "nova_turma_secretaria.html.j2", turma=turma_ctx
        )
        subject_sec = f"Nova turma cadastrada - {ctx['treinamento_nome']}"
        for email in emails_secretaria:
            send_email(email, subject_sec, html_sec)


def notificar_atualizacao_turma(
    turma: "TurmaTreinamento", diff: Dict[str, Any], instrutor_antigo: "Instrutor" | None
) -> None:
    """Notifica secretaria e instrutores sobre alterações em uma turma."""
    treinamento = getattr(turma, "treinamento", None)
    nome_treinamento = getattr(treinamento, "nome", "")

    emails_secretaria = listar_emails_secretaria()
    if emails_secretaria and diff:
        turma_ctx = build_turma_context(turma)
        html_sec = render_email_template(
            "turma_atualizada_secretaria.html.j2", turma=turma_ctx
        )
        subject_sec = f"Turma atualizada - {nome_treinamento}"
        for email in emails_secretaria:
            send_email(email, subject_sec, html_sec)

    instrutor_atual = getattr(turma, "instrutor", None)
    if instrutor_antigo != instrutor_atual:
        if instrutor_antigo and getattr(instrutor_antigo, "email", None):
            html_rem = render_email_template(
                "instrutor_removido.html.j2",
                instrutor_nome=getattr(instrutor_antigo, "nome", ""),
                treinamento_nome=nome_treinamento,
                data_inicio=turma.data_inicio.strftime("%d/%m/%Y") if getattr(turma, "data_inicio", None) else "",
            )
            subject_rem = f"Remoção de turma - {nome_treinamento}"
            send_email(instrutor_antigo.email, subject_rem, html_rem)
        if instrutor_atual and getattr(instrutor_atual, "email", None):
            html_des = render_email_template(
                "instrutor_designado.html.j2",
                instrutor_nome=getattr(instrutor_atual, "nome", ""),
                treinamento_nome=nome_treinamento,
                data_inicio=turma.data_inicio.strftime("%d/%m/%Y") if getattr(turma, "data_inicio", None) else "",
                data_fim=turma.data_fim.strftime("%d/%m/%Y") if getattr(turma, "data_fim", None) else None,
                horario=getattr(turma, "horario", "-") or "-",
                local_realizacao=getattr(turma, "local_realizacao", "-") or "-",
            )
            subject_des = f"Nova turma designada - {nome_treinamento}"
            send_email(instrutor_atual.email, subject_des, html_des)
