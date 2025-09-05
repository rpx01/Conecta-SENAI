from email.message import EmailMessage
import smtplib
import ssl
import threading
from flask import current_app


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


def send_email_via_smtp(app, message: EmailMessage):
    """Envio SMTP com timeout curto para não travar o worker.

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
    timeout = int(cfg.get("MAIL_TIMEOUT", 12))

    try:
        if use_ssl:
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
    except Exception:
        # Loga a stack completa mas NÃO levanta para não quebrar o fluxo do
        # /forgot
        app.logger.exception(
            "Falha ao enviar e-mail para %s", message["To"]
        )


def queue_reset_email(to_email: str, token: str):
    """Dispara em thread para não bloquear o request."""
    app = current_app._get_current_object()
    base_url = app.config.get(
        "APP_BASE_URL", "https://conecta-senai.up.railway.app"
    )
    reset_url = f"{base_url}/reset?token={token}"
    msg = _build_reset_message(to_email, reset_url)

    t = threading.Thread(target=send_email_via_smtp, args=(app, msg), daemon=True)
    t.start()
