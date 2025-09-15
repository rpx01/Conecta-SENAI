from __future__ import annotations
import os
import base64
from typing import (
    Iterable,
    Optional,
    Dict,
    Any,
    List,
    Union,
    TYPE_CHECKING,
    Callable,
)
import logging
import re
import time as time_module
import threading
from collections import deque

import resend
from flask import current_app, render_template
from types import SimpleNamespace
from datetime import time

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.models.treinamento import TurmaTreinamento
    from src.models.instrutor import Instrutor

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
# Permite definir o remetente tanto via MAIL_FROM quanto RESEND_FROM
DEFAULT_FROM = os.getenv("MAIL_FROM") or os.getenv(
    "RESEND_FROM", "no-reply@example.com"
)
DEFAULT_REPLY_TO = os.getenv("RESEND_REPLY_TO")

Address = Union[str, Iterable[str]]


class RateLimiter:
    """Decorator que limita a taxa de execução de uma função."""

    def __init__(self, max_calls: int, period: int = 1) -> None:
        self.calls: deque[float] = deque()
        self.period = period
        self.max_calls = max_calls
        self.lock = threading.Lock()

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self.lock:
                now = time_module.monotonic()
                while self.calls and now - self.calls[0] > self.period:
                    self.calls.popleft()

                if len(self.calls) >= self.max_calls:
                    sleep_for = (self.calls[0] + self.period) - now
                    if sleep_for > 0:
                        time_module.sleep(sleep_for)
                        now = time_module.monotonic()
                        while self.calls and now - self.calls[0] > self.period:
                            self.calls.popleft()

                self.calls.append(time_module.monotonic())

            return func(*args, **kwargs)

        return wrapper


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


@RateLimiter(max_calls=2, period=1)
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
        log.error(
            "Erro ao renderizar template de e-mail %s: %s",
            nome_template,
            exc,
        )
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
                "Falha ao enviar notificação de planejamento para %s: %s",
                destinatario,
                exc,
            )


def enviar_convocacao(
    inscricao: Any, turma: Any, send_email_fn: Callable[..., Any] = send_email
) -> None:
    """Envia e-mail de convocação para um inscrito."""
    treinamento = getattr(turma, "treinamento", None)
    if treinamento is None:
        raise ValueError("Turma sem treinamento associado")

    destinatario = getattr(inscricao, "email", "")
    log.info(f"Tentando enviar e-mail de convocação para {destinatario}")

    is_teoria_online = bool(getattr(turma, "teoria_online", False))
    has_tem_pratica = bool(getattr(treinamento, "tem_pratica", False))

    data_inicio = getattr(turma, "data_inicio", None)
    data_fim = getattr(turma, "data_fim", None)
    periodo = ""
    if data_inicio and data_fim:
        periodo = (
            f"De {data_inicio.strftime('%d/%m/%Y')} "
            f"a {data_fim.strftime('%d/%m/%Y')}"
        )

    instrutor = getattr(getattr(turma, "instrutor", None), "nome", "A definir")
    local_realizacao = getattr(turma, "local_realizacao", "")

    html = render_template(
        "email/convocacao.html.j2",
        nome=getattr(inscricao, "nome", ""),
        nome_do_treinamento=getattr(treinamento, "nome", ""),
        periodo=periodo,
        horario=getattr(turma, "horario", ""),
        carga_horaria=getattr(treinamento, "carga_horaria", ""),
        instrutor=instrutor,
        local_de_realizacao=local_realizacao,
        email_fornecido_na_inscricao=destinatario,
        local_da_pratica=local_realizacao,
        teoria_online=is_teoria_online,
        tem_pratica=has_tem_pratica,
    )

    attachments: List[Dict[str, Any]] = []
    if is_teoria_online:
        try:
            file_path = os.path.join(
                current_app.static_folder,
                "docs",
                "Tutorial de Acesso e Navegação - Aluno Anglo.pdf",
            )
            file_name = "Tutorial de Acesso e Navegação - Aluno Anglo.pdf"
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            attachments.append({"filename": file_name, "content": encoded})
        except FileNotFoundError:
            current_app.logger.error("Arquivo de tutorial não encontrado.")

    data_inicio_str = data_inicio.strftime("%d/%m/%Y") if data_inicio else ""
    subject = (
        f"Convocação: {getattr(treinamento, 'nome', '')} — {data_inicio_str}"
    )
    if send_email_fn is send_email:
        send_email_fn(
            to=destinatario,
            subject=subject,
            html=html,
            attachments=attachments,
        )
    else:
        send_email_fn(to=destinatario, subject=subject, html=html)
    log.info(f"E-mail de convocação enviado com sucesso para {destinatario}")


def listar_emails_secretaria() -> List[str]:
    """Retorna e-mails da secretaria de treinamentos."""
    from src.models.secretaria_treinamentos import (
        SecretariaTreinamentos,
    )  # lazy import

    registros = SecretariaTreinamentos.query.all()
    return [r.email for r in registros if getattr(r, "email", None)]


def send_turma_alterada_secretaria(
    emails: Iterable[str], dados_antigos: Dict[str, Any], turma: Any
) -> None:
    """Envia e-mail comparando dados antigos e novos de uma turma."""
    turma_ctx = build_turma_context(turma)
    subject = (
        "Alteração de Agendamento de Turma: "
        f"{turma_ctx.treinamento.nome} - Turma {turma_ctx.nome}"
    )
    html = render_email_template(
        "turma_alterada_secretaria.html.j2",
        dados_antigos=dados_antigos,
        turma=turma_ctx,
    )
    for email in emails:
        send_email(email, subject, html)


def send_turma_alterada_email(dados_antigos: dict, dados_novos: dict):
    """Envia e-mail à secretaria informando alteração de uma turma."""
    try:
        recipients = listar_emails_secretaria()
        if not recipients:
            current_app.logger.warning(
                "Nenhum e-mail de secretaria encontrado para "
                "notificação de turma alterada."
            )
            return

        html_body = render_template(
            "email/turma_alterada_secretaria.html.j2",
            dados_antigos=dados_antigos,
            dados_novos=dados_novos,
        )

        subject = (
            "Alteração de Agendamento de Turma: "
            f"{dados_novos.get('treinamento_nome')}"
        )
        for idx, email in enumerate(recipients):
            send_email(email, subject, html_body)
            if idx < len(recipients) - 1:
                time_module.sleep(0.5)
        current_app.logger.info(
            (
                "E-mail de alteração da turma "
                f"'{dados_novos.get('treinamento_nome')}' "
                "enviado para a secretaria."
            )
        )
    except Exception as e:  # pragma: no cover - log de erro
        current_app.logger.error(
            f"Falha ao enviar e-mail de turma alterada: {e}", exc_info=True
        )


def send_nova_turma_instrutor_email(
    turma: "TurmaTreinamento",
    instrutor: "Instrutor",
) -> None:
    """Envia um e-mail para o instrutor informando sobre a nova turma."""
    if not instrutor or not getattr(instrutor, "email", None):
        return

    treinamento = getattr(turma, "treinamento", None)
    html = render_email_template(
        "nova_turma_instrutor.html.j2",
        instrutor_nome=getattr(instrutor, "nome", ""),
        treinamento_nome=getattr(treinamento, "nome", ""),
        data_inicio=(
            turma.data_inicio.strftime("%d/%m/%Y")
            if getattr(turma, "data_inicio", None)
            else ""
        ),
        data_fim=(
            turma.data_fim.strftime("%d/%m/%Y")
            if getattr(turma, "data_fim", None)
            else None
        ),
        horario=getattr(turma, "horario", "-") or "-",
        local_realizacao=getattr(turma, "local_realizacao", "-") or "-",
    )
    subject = f"Nova turma designada - {getattr(treinamento, 'nome', '')}"
    send_email(instrutor.email, subject, html)


def notificar_nova_turma(turma: "TurmaTreinamento") -> None:
    """Notifica instrutor e secretaria sobre criação de nova turma."""
    treinamento = getattr(turma, "treinamento", None)
    if not treinamento:
        return

    fmt = "%d/%m/%Y"
    data_inicio = (
        turma.data_inicio.strftime(fmt)
        if getattr(turma, "data_inicio", None)
        else ""
    )
    data_fim = (
        turma.data_fim.strftime(fmt)
        if getattr(turma, "data_fim", None)
        else None
    )
    ctx = {
        "treinamento_nome": getattr(treinamento, "nome", ""),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "horario": getattr(turma, "horario", "-") or "-",
        "local_realizacao": getattr(turma, "local_realizacao", "-") or "-",
    }

    instrutor = getattr(turma, "instrutor", None)
    if instrutor and getattr(instrutor, "email", None):
        send_nova_turma_instrutor_email(turma, instrutor)

    emails_secretaria = listar_emails_secretaria()
    if emails_secretaria:
        turma_ctx = build_turma_context(turma)
        html_sec = render_email_template(
            "nova_turma_secretaria.html.j2",
            turma=turma_ctx,
        )
        subject_sec = f"Nova turma cadastrada - {ctx['treinamento_nome']}"
        for email in emails_secretaria:
            send_email(email, subject_sec, html_sec)


def notificar_atualizacao_turma(
    turma: "TurmaTreinamento",
    diff: Dict[str, Any],
    instrutor_antigo: "Instrutor" | None,
    *,
    notificar_secretaria: bool = True,
) -> None:
    """Notifica secretaria e instrutores sobre alterações em uma turma."""
    treinamento = getattr(turma, "treinamento", None)
    nome_treinamento = getattr(treinamento, "nome", "")

    emails_secretaria = listar_emails_secretaria()
    if notificar_secretaria and emails_secretaria and diff:
        turma_ctx = build_turma_context(turma)
        fmt = "%d/%m/%Y"
        # Monta dados antigos com base no diff
        dados_antigos = {
            "nome": turma_ctx.nome,
            "data_inicio": diff.get(
                "data_inicio",
                (
                    turma_ctx.data_inicio.strftime(fmt)
                    if turma_ctx.data_inicio
                    else None,
                    None,
                ),
            )[0],
            "data_termino": diff.get(
                "data_fim",
                (
                    turma_ctx.data_termino.strftime(fmt)
                    if turma_ctx.data_termino
                    else None,
                    None,
                ),
            )[0],
            "local": diff.get("local_realizacao", (turma_ctx.local, None))[0],
            "instrutor_nome": diff.get(
                "instrutor",
                (
                    turma_ctx.instrutor.nome
                    if turma_ctx.instrutor
                    else "A definir",
                    None,
                ),
            )[0],
        }
        old_horario = diff.get("horario", (None, None))[0]
        if old_horario:
            partes = str(old_horario).split("-")
            hora_ini = _parse_time(partes[0]) or turma_ctx.horario_inicio
            hora_fim = (
                _parse_time(partes[1]) if len(partes) > 1 else None
            )
            hora_fim = hora_fim or turma_ctx.horario_fim
        else:
            hora_ini = turma_ctx.horario_inicio
            hora_fim = turma_ctx.horario_fim
        dados_antigos["horario_inicio"] = hora_ini.strftime("%H:%M")
        dados_antigos["horario_fim"] = hora_fim.strftime("%H:%M")

        dados_novos = {
            "treinamento_nome": turma_ctx.treinamento.nome,
            "treinamento_codigo": getattr(treinamento, "codigo", ""),
            "periodo": (
                f"{turma_ctx.data_inicio.strftime('%d/%m/%Y')} a "
                f"{turma_ctx.data_termino.strftime('%d/%m/%Y')}"
                if turma_ctx.data_inicio and turma_ctx.data_termino
                else ""
            ),
            "horario": getattr(turma, "horario", ""),
            "carga_horaria": getattr(treinamento, "carga_horaria", None),
            "instrutor_nome": (
                turma_ctx.instrutor.nome
                if turma_ctx.instrutor
                else "Não definido"
            ),
            "local_realizacao": turma_ctx.local,
            "teoria_online": getattr(turma, "teoria_online", False),
            "tem_pratica": getattr(treinamento, "tem_pratica", False),
            "local_pratica": getattr(turma, "local_pratica", None),
        }

        send_turma_alterada_email(dados_antigos, dados_novos)
        time_module.sleep(0.5)

    instrutor_atual = getattr(turma, "instrutor", None)

    # ``instrutor_antigo`` pode ser uma instância ou apenas o ID.
    instrutor_antigo_obj = instrutor_antigo
    if instrutor_antigo_obj and not getattr(
        instrutor_antigo_obj, "email", None
    ):
        try:  # tenta carregar o instrutor a partir do ID
            from src.models.instrutor import Instrutor  # lazy import
            from src.models import db

            instrutor_antigo_obj = db.session.get(
                Instrutor, instrutor_antigo_obj
            )
        except Exception:  # pragma: no cover - fallback silencioso
            instrutor_antigo_obj = None

    antigo_id = getattr(instrutor_antigo_obj, "id", None)
    atual_id = getattr(instrutor_atual, "id", None)

    if antigo_id and antigo_id != atual_id:
        if getattr(instrutor_antigo_obj, "email", None):
            turma_ctx = SimpleNamespace(
                treinamento=SimpleNamespace(
                    nome=getattr(treinamento, "nome", ""),
                    codigo=getattr(treinamento, "codigo", ""),
                    carga_horaria=getattr(treinamento, "carga_horaria", None),
                    tem_pratica=getattr(treinamento, "tem_pratica", False),
                ),
                data_inicio=getattr(turma, "data_inicio", None),
                data_termino=getattr(turma, "data_fim", None),
                horario=getattr(turma, "horario", ""),
                local=getattr(turma, "local_realizacao", ""),
                teoria_online=getattr(turma, "teoria_online", False),
                local_pratica=getattr(turma, "local_pratica", None),
            )

            html_rem = render_email_template(
                "instrutor_removido.html.j2",
                instrutor_nome=getattr(instrutor_antigo_obj, "nome", ""),
                turma=turma_ctx,
            )
            subject_rem = f"Remanejamento de Turma - {nome_treinamento}"
            send_email(instrutor_antigo_obj.email, subject_rem, html_rem)
            time_module.sleep(0.5)

    if (
        atual_id
        and antigo_id != atual_id
        and getattr(instrutor_atual, "email", None)
    ):
        send_nova_turma_instrutor_email(turma, instrutor_atual)


class EmailService:
    """Serviço de envio de e-mails com suporte a anexos."""

    def _send_mail(
        self,
        subject: str,
        recipients: Iterable[str],
        template: str,
        context: Dict[str, Any],
        attachment_path: str | None = None,
    ) -> None:
        """Renderiza o template e envia o e-mail.

        Se ``attachment_path`` for fornecido e existir, o arquivo será anexado
        ao e-mail.
        """

        template_obj = current_app.jinja_env.get_or_select_template(template)
        html = template_obj.render(**context)

        attachments: List[Dict[str, Any]] = []
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            file_name = os.path.basename(attachment_path)
            attachments.append({"filename": file_name, "content": encoded})
            current_app.logger.info(f"Anexando '{file_name}' ao e-mail.")

        send_email(
            to=list(recipients),
            subject=subject,
            html=html,
            attachments=attachments,
        )

    def send_convocacao_email(self, user: Any, turma: Any) -> None:
        """Envia e-mail de convocação com anexo quando necessário."""

        subject = (
            f"Convocação: {turma.treinamento.nome} — "
            f"{turma.data_inicio.strftime('%d/%m/%Y')}"
        )

        attachment: str | None = None
        if getattr(turma, "teoria_online", False):
            attachment = os.path.join(
                current_app.static_folder,
                "docs",
                "Tutorial de Acesso e Navegação - Aluno Anglo.pdf",
            )

        self._send_mail(
            subject=subject,
            recipients=[user.email],
            template="email/convocacao.html.j2",
            context={"user": user, "turma": turma},
            attachment_path=attachment,
        )
