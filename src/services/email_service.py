# flake8: noqa
import os
import ssl
import smtplib
import socket
import time
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import msal

log = logging.getLogger(__name__)

def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "t", "yes", "on"}

class EmailClient:
    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "GMAIL")
        self.from_addr = os.getenv("EMAIL_FROM") or os.getenv("MAIL_DEFAULT_SENDER")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Conecta SENAI")

        if self.provider == "GMAIL":
            self.server = os.getenv(
                "SMTP_SERVER", os.getenv("MAIL_SERVER", "smtp.gmail.com")
            )
            self.port = int(
                os.getenv("SMTP_PORT", os.getenv("MAIL_PORT", "587"))
            )
        else:  # OUTLOOK or default
            self.server = os.getenv(
                "SMTP_SERVER", os.getenv("MAIL_SERVER", "smtp.office365.com")
            )
            self.port = int(
                os.getenv("SMTP_PORT", os.getenv("MAIL_PORT", "587"))
            )
        self.username = os.getenv("SMTP_USERNAME", os.getenv("MAIL_USERNAME", ""))
        self.password = os.getenv("SMTP_PASSWORD", os.getenv("MAIL_PASSWORD", ""))
        self.client_id = os.getenv("CLIENT_ID", "")
        self.tenant_id = os.getenv("TENANT_ID", "")
        self.client_secret = os.getenv("CLIENT_SECRET", "")
        self.use_tls = _env_bool("SMTP_USE_TLS", True)
        self.use_ssl = _env_bool("SMTP_USE_SSL", False)
        self.timeout = int(os.getenv("SMTP_TIMEOUT", os.getenv("MAIL_TIMEOUT", "15")))
        self.max_retries = 3

    def _get_oauth2_token(self) -> str:
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.ConfidentialClientApplication(
            self.client_id, authority=authority, client_credential=self.client_secret
        )
        result = app.acquire_token_for_client(
            scopes=["https://outlook.office365.com/.default"]
        )
        token = result.get("access_token")
        if not token:
            raise Exception(result.get("error_description", "failed to obtain token"))
        return token

    def _connect(self):
        if self.use_ssl:
            smtp = smtplib.SMTP_SSL(self.server, self.port, timeout=self.timeout)
        else:
            smtp = smtplib.SMTP(self.server, self.port, timeout=self.timeout)
            smtp.ehlo()
            if self.use_tls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()

        if self.provider == "OUTLOOK":
            if self.username:
                token = self._get_oauth2_token()
                auth_string = (
                    f"user={self.username}\1auth=Bearer {token}\1\1".encode("utf-8")
                )
                smtp.auth("XOAUTH2", lambda x: auth_string)
        elif self.provider == "GMAIL":
            if self.username and self.password:
                smtp.login(self.username, self.password)

        return smtp

    def send_mail(self, to, subject, html_body, text_body=None, reply_to=None,
                  cc=None, bcc=None, attachments=None):
        if not self.from_addr:
            raise ValueError("EMAIL_FROM não configurado")
        to_list = [to] if isinstance(to, str) else list(to)
        cc = cc or []
        bcc = bcc or []
        recipients = to_list + list(cc) + list(bcc)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_addr}>"
        msg["To"] = ", ".join(to_list)
        if cc:
            msg["Cc"] = ", ".join(cc)
        if reply_to:
            msg["Reply-To"] = reply_to
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        for att in attachments or []:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(att["bytes"])
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{att["filename"]}"')
            msg.attach(part)

        attempt = 1
        backoff = 1
        while True:
            start = time.time()
            try:
                log.info("EMAIL_SEND_START", extra={"to": to_list, "subject": subject, "attempt": attempt})
                with self._connect() as smtp:
                    smtp.sendmail(self.from_addr, recipients, msg.as_string())
                elapsed = int((time.time() - start) * 1000)
                log.info("EMAIL_SEND_SUCCESS", extra={"to": to_list, "subject": subject, "attempt": attempt, "elapsed_ms": elapsed})
                return True
            except smtplib.SMTPAuthenticationError as e:
                log.error("EMAIL_SEND_FAILURE", extra={"to": to_list, "subject": subject, "attempt": attempt, "error_kind": "auth", "error": str(e)})
                raise
            except (socket.gaierror, TimeoutError, socket.timeout, smtplib.SMTPConnectError,
                    smtplib.SMTPServerDisconnected, smtplib.SMTPResponseException, OSError) as e:
                if isinstance(e, socket.gaierror):
                    kind = "dns"
                elif isinstance(e, (TimeoutError, socket.timeout)):
                    kind = "timeout"
                elif isinstance(e, OSError) and getattr(e, "errno", None) in (101, 113):
                    kind = "no_route_to_host"
                else:
                    kind = "network"
                elapsed = int((time.time() - start) * 1000)
                log.warning("EMAIL_SEND_FAILURE", extra={"to": to_list, "subject": subject, "attempt": attempt, "elapsed_ms": elapsed, "error_kind": kind, "error": str(e)})
                if attempt >= self.max_retries:
                    log.error("EMAIL_SEND_FAILURE", extra={"to": to_list, "subject": subject, "attempt": attempt, "elapsed_ms": elapsed, "error_kind": kind, "error": str(e)})
                    raise
                time.sleep(backoff)
                attempt += 1
                backoff = backoff * 2 + 1
            except Exception as e:
                elapsed = int((time.time() - start) * 1000)
                log.error("EMAIL_SEND_FAILURE", extra={"to": to_list, "subject": subject, "attempt": attempt, "elapsed_ms": elapsed, "error_kind": "unknown", "error": str(e)})
                raise

    def test_smtp_connection(self):
        try:
            with self._connect() as smtp:
                smtp.noop()
            log.info("SMTP connection test succeeded")
            return True
        except Exception as e:
            log.error(
                "SMTP connection test failed",
                extra={"error": str(e)},
                exc_info=e,
            )
            return False
