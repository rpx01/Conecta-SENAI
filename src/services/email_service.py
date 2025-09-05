from flask import current_app, render_template
from threading import Thread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging


def _send_email_via_smtp(app, subject, recipient, body_html, body_text=None):
    """Executa dentro de uma thread, mas com app_context válido."""
    with app.app_context():
        try:
            cfg = app.config
            host = cfg.get("MAIL_SERVER")
            port = int(cfg.get("MAIL_PORT", 587))
            username = cfg.get("MAIL_USERNAME")
            password = cfg.get("MAIL_PASSWORD")
            use_tls = bool(cfg.get("MAIL_USE_TLS", True))
            use_ssl = bool(cfg.get("MAIL_USE_SSL", False))
            sender = cfg.get("MAIL_DEFAULT_SENDER") or username

            if not host or not sender:
                logging.error(
                    "Config de e-mail ausente: "
                    "MAIL_SERVER/MAIL_DEFAULT_SENDER."
                )
                return

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient

            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
            if body_html:
                msg.attach(MIMEText(body_html, "html", "utf-8"))

            server = None
            try:
                if use_ssl:
                    server = smtplib.SMTP_SSL(host, port, timeout=30)
                else:
                    server = smtplib.SMTP(host, port, timeout=30)
                    if use_tls:
                        server.starttls()

                if username and password:
                    server.login(username, password)

                server.sendmail(sender, [recipient], msg.as_string())
                logging.info(f"E-mail de recuperação enviado para {recipient}")
            finally:
                if server:
                    try:
                        server.quit()
                    except Exception:
                        logging.debug("SMTP quit falhou (ignorado).")
        except Exception:
            logging.exception("Falha ao enviar e-mail (recuperação de senha).")


def send_email_async(subject, recipient, body_html, body_text=None):
    """Captura o app atual e dispara a thread sem bloquear a requisição."""
    app = current_app._get_current_object()
    th = Thread(
        target=_send_email_via_smtp,
        args=(app, subject, recipient, body_html, body_text),
        daemon=True,
    )
    th.start()
    return th


# Compatibilidade: antiga função para envio de reset que utiliza
# templates existentes

def queue_reset_email(to_email: str, token: str):
    """Mantida para compatibilidade. Monta e-mail de reset e envia de forma
    assíncrona."""
    app = current_app._get_current_object()
    base_url = app.config.get(
        "APP_BASE_URL", "https://conecta-senai.up.railway.app"
    )
    reset_url = f"{base_url}/reset?token={token}"
    try:
        body_html = render_template(
            "emails/reset_password.html", reset_url=reset_url
        )
    except Exception:
        body_html = (
            f"<p>Olá!</p><p>Use o link abaixo para redefinir sua senha:</p>"
            f"<p><a href='{reset_url}'>{reset_url}</a></p>"
            "<p>Se você não solicitou, ignore este e-mail.</p>"
        )
    subject = "Conecta SENAI – Redefinição de senha"
    send_email_async(subject, to_email, body_html)
