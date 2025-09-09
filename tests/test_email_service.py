import socket
import smtplib
from unittest.mock import MagicMock, patch
from email import message_from_string

import pytest

from src.services.email_service import EmailClient


@pytest.fixture
def email_env(monkeypatch):
    monkeypatch.setenv("EMAIL_FROM", "no-reply@example.com")
    monkeypatch.setenv("EMAIL_FROM_NAME", "Conecta SENAI")
    monkeypatch.setenv("SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.setenv("CLIENT_ID", "cid")
    monkeypatch.setenv("TENANT_ID", "tid")
    monkeypatch.setenv("CLIENT_SECRET", "sec")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_USE_SSL", "false")
    monkeypatch.setenv("SMTP_TIMEOUT", "15")
    monkeypatch.setattr(
        "src.services.email_service.EmailClient._get_oauth2_token",
        lambda self: "token",
    )


def _mock_smtp(instance):
    instance.__enter__.return_value = instance
    mock_smtp = MagicMock(return_value=instance)
    return mock_smtp


def test_send_mail_success(email_env):
    instance = MagicMock()
    with patch("src.services.email_service.smtplib.SMTP", _mock_smtp(instance)):
        client = EmailClient()
        ok = client.send_mail(
            to="dest@example.com",
            subject="Teste",
            html_body="<p>Olá</p>",
            text_body="Olá",
            reply_to="reply@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            attachments=[{"filename": "a.txt", "bytes": b"hello"}],
        )
        assert ok
    args = instance.sendmail.call_args[0]
    msg = message_from_string(args[2])
    assert msg["From"] == "Conecta SENAI <no-reply@example.com>"
    assert msg["Reply-To"] == "reply@example.com"
    assert msg["Cc"] == "cc@example.com"
    assert "bcc@example.com" not in args[2]
    part = next(p for p in msg.walk() if p.get_filename() == "a.txt")
    assert part.get_payload(decode=True) == b"hello"


def test_send_mail_timeout(email_env):
    instance = MagicMock()
    instance.sendmail.side_effect = socket.timeout()
    with patch("src.services.email_service.smtplib.SMTP", _mock_smtp(instance)), \
         patch("src.services.email_service.time.sleep") as sleep:
        client = EmailClient()
        with pytest.raises(socket.timeout):
            client.send_mail("a@b", "s", "<p>hi</p>")
        assert sleep.call_args_list[0][0][0] == 1
        assert sleep.call_args_list[1][0][0] == 3


def test_send_mail_dns_error(email_env):
    with patch("src.services.email_service.smtplib.SMTP", side_effect=socket.gaierror("dns")), \
         patch("src.services.email_service.time.sleep") as sleep:
        client = EmailClient()
        with pytest.raises(socket.gaierror):
            client.send_mail("a@b", "s", "<p>hi</p>")
        assert sleep.call_args_list[0][0][0] == 1
        assert sleep.call_args_list[1][0][0] == 3


def test_send_mail_auth_error(email_env):
    instance = MagicMock()
    instance.auth.side_effect = smtplib.SMTPAuthenticationError(535, b"5.7.3 auth failed")
    with patch("src.services.email_service.smtplib.SMTP", _mock_smtp(instance)):
        client = EmailClient()
        with pytest.raises(smtplib.SMTPAuthenticationError):
            client.send_mail("a@b", "s", "<p>hi</p>")
    assert instance.auth.called


def test_send_mail_no_route(email_env):
    instance = MagicMock()
    instance.sendmail.side_effect = OSError(113, "No route to host")
    with patch("src.services.email_service.smtplib.SMTP", _mock_smtp(instance)), \
         patch("src.services.email_service.time.sleep") as sleep:
        client = EmailClient()
        with pytest.raises(OSError):
            client.send_mail("a@b", "s", "<p>hi</p>")
        assert sleep.call_count == 2


def test_send_mail_backoff_success(email_env):
    call = {"n": 0}
    instance = MagicMock()

    def side_effect(*args, **kwargs):
        call["n"] += 1
        if call["n"] < 3:
            raise OSError(101, "down")
        return True

    instance.sendmail.side_effect = side_effect
    with patch("src.services.email_service.smtplib.SMTP", _mock_smtp(instance)), \
         patch("src.services.email_service.time.sleep") as sleep:
        client = EmailClient()
        assert client.send_mail("a@b", "s", "<p>hi</p>")
        assert sleep.call_args_list[0][0][0] == 1
        assert sleep.call_args_list[1][0][0] == 3
        assert call["n"] == 3


def test_test_smtp_connection_oauth(email_env):
    instance = MagicMock()
    with patch("src.services.email_service.smtplib.SMTP", _mock_smtp(instance)):
        client = EmailClient()
        assert client.test_smtp_connection()
    assert instance.auth.called
