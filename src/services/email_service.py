from email.message import EmailMessage
import json
from pathlib import Path
import smtplib
import ssl
import threading
import time
import socket

from flask import current_app


def _connect_gmail(user: str, pwd: str, timeout: int = 15):
    """Connect to Gmail using IPv4 and fallback from TLS to SSL."""
    last_err = None
    for host, port, mode in [
        ("smtp.gmail.com", 587, "tls"),
        ("smtp.gmail.com", 465, "ssl"),
    ]:
        try:
            addr = next(
                a[4]
                for a in socket.getaddrinfo(
                    host, port, socket.AF_INET, socket.SOCK_STREAM
                )
            )
            sock = socket.create_connection(addr, timeout=timeout)
            sock.close()

            if mode == "tls":
                s = smtplib.SMTP(host, port, timeout=timeout)
                s.ehlo()
                s.starttls()
                s.ehlo()
            else:
                s = smtplib.SMTP_SSL(host, port, timeout=timeout)
            s.login(user, pwd)
            return s
        except Exception as e:  # pragma: no cover - network dependent
            last_err = e
    raise last_err


def _build_reset_message(to_email: str, reset_url: str) -> EmailMessage:
    cfg = current_app.config
    msg = EmailMessage()
    msg["Subject"] = "Conecta SENAI – Redefinição de senha"
    msg["From"] = cfg.get("MAIL_DEFAULT_SENDER")
    msg["To"] = to_email

    text = (
        f"Olá,\n\nUse o link abaixo para redefinir sua senha:\n{reset_url}\n\n"
        "Se você não solicitou, ignore esta mensagem."
    )
    html = f"""
        <p>Olá,</p>
        <p>Use o link abaixo para redefinir sua senha:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>Se você não solicitou, ignore esta mensagem.</p>
    """

    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


def _enqueue_email(app, message: EmailMessage) -> None:
    """Persiste e-mail para reprocessamento futuro."""
    queue_path = Path(app.config.get("MAIL_QUEUE_PATH", "email_queue.jsonl"))
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "to": message["To"],
        "subject": message.get("Subject", ""),
        "raw": message.as_string(),
    }
    with queue_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
    app.logger.info("E-mail enfileirado para %s", message["To"])


def send_email_via_smtp(app, message: EmailMessage) -> None:
    """Envio SMTP com timeout curto e retry com backoff exponencial.

    Como o envio ocorre em uma thread separada, ``current_app`` não está
    disponível. Por isso, passamos explicitamente a instância de aplicação
    para acessar configuração e logger sem depender de contexto de
    requisição.
    """
    cfg = app.config

    server = cfg.get("MAIL_SERVER")
    port = int(cfg.get("MAIL_PORT", 587))
    username = cfg.get("MAIL_USERNAME")
    password = cfg.get("MAIL_PASSWORD")
    use_tls = cfg.get("MAIL_USE_TLS", True)
    use_ssl = cfg.get("MAIL_USE_SSL", False)
    if cfg.get("MAIL_SUPPRESS_SEND"):
        app.logger.info("Envio de e-mail suprimido para %s", message["To"])
        return
    timeout = int(cfg.get("MAIL_TIMEOUT", 12))
    max_attempts = int(cfg.get("MAIL_MAX_RETRIES", 3))

    delay = 1
    for attempt in range(1, max_attempts + 1):
        try:
            if server == "smtp.gmail.com":
                with _connect_gmail(
                    username, password, timeout=timeout
                ) as smtp:
                    smtp.send_message(message)
            elif use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    server, port, timeout=timeout, context=context
                ) as smtp:
                    if username and password:
                        smtp.login(username, password)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(server, port, timeout=timeout) as smtp:
                    smtp.ehlo()
                    if use_tls:
                        context = ssl.create_default_context()
                        smtp.starttls(context=context)
                        smtp.ehlo()
                    if username and password:
                        smtp.login(username, password)
                    smtp.send_message(message)

            app.logger.info("E-mail enviado para %s", message["To"])
            return
        except OSError as e:
            if getattr(e, "errno", None) == 101:
                app.logger.error(
                    "Falha ao enviar e-mail para %s: rede indisponível"
                    " (tentativa %s/%s)",
                    message["To"],
                    attempt,
                    max_attempts,
                )
            else:
                app.logger.exception(
                    "Falha ao enviar e-mail para %s (tentativa %s/%s)",
                    message["To"],
                    attempt,
                    max_attempts,
                )
        except Exception:
            app.logger.exception(
                "Falha ao enviar e-mail para %s (tentativa %s/%s)",
                message["To"],
                attempt,
                max_attempts,
            )

        if attempt == max_attempts:
            _enqueue_email(app, message)
            return
        time.sleep(delay)
        delay *= 2


def queue_reset_email(to_email: str, token: str):
    """Dispara em thread para não bloquear o request."""
    app = current_app._get_current_object()
    base_url = app.config.get(
        "APP_BASE_URL", "https://conecta-senai.up.railway.app"
    )
    reset_url = f"{base_url}/reset?token={token}"
    msg = _build_reset_message(to_email, reset_url)

    t = threading.Thread(
        target=send_email_via_smtp,
        args=(app, msg),
        daemon=True,
    )
    t.start()
