import json
import logging
from email.message import EmailMessage
from types import SimpleNamespace

import pytest

from src.services import email_service


def _make_message():
    msg = EmailMessage()
    msg["To"] = "user@example.com"
    msg["From"] = "noreply@example.com"
    msg["Subject"] = "teste"
    msg.set_content("hello")
    return msg


def _patch_smtp(monkeypatch, smtp_class):
    monkeypatch.setattr(email_service, "smtplib", SimpleNamespace(SMTP=smtp_class, SMTP_SSL=smtp_class))


@pytest.fixture
def email_app(app, tmp_path):
    app.config.update(
        MAIL_SERVER="smtp.example.com",
        MAIL_PORT=25,
        MAIL_USE_TLS=False,
        MAIL_USE_SSL=False,
        MAIL_USERNAME="",
        MAIL_PASSWORD="",
        MAIL_MAX_RETRIES=3,
        MAIL_QUEUE_PATH=str(tmp_path / "queue.jsonl"),
    )
    return app


class _BaseSMTP:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def ehlo(self):
        pass

    def starttls(self, context=None):
        pass

    def login(self, username, password):
        pass


class SuccessSMTP(_BaseSMTP):
    def send_message(self, message):
        return True


class FlakySMTP(_BaseSMTP):
    attempts = 0

    def send_message(self, message):
        self.__class__.attempts += 1
        if self.attempts == 1:
            raise OSError(101, "network down")
        return True


class FailingSMTP(_BaseSMTP):
    attempts = 0

    def send_message(self, message):
        self.__class__.attempts += 1
        raise OSError(101, "network down")


def test_send_email_success_first_try(email_app, monkeypatch, caplog, tmp_path):
    _patch_smtp(monkeypatch, SuccessSMTP)
    msg = _make_message()
    with caplog.at_level(logging.INFO):
        email_service.send_email_via_smtp(email_app, msg)
    assert any("E-mail enviado" in r.message for r in caplog.records)
    assert not (tmp_path / "queue.jsonl").exists()


def test_send_email_success_after_retry(email_app, monkeypatch, caplog, tmp_path):
    FlakySMTP.attempts = 0
    _patch_smtp(monkeypatch, FlakySMTP)
    monkeypatch.setattr(email_service.time, "sleep", lambda s: None)
    msg = _make_message()
    with caplog.at_level(logging.INFO):
        email_service.send_email_via_smtp(email_app, msg)
    assert FlakySMTP.attempts == 2
    assert any("tentativa 1/3" in r.message for r in caplog.records)
    assert any("E-mail enviado" in r.message for r in caplog.records)
    assert not (tmp_path / "queue.jsonl").exists()


def test_send_email_failure_queue(email_app, monkeypatch, caplog, tmp_path):
    FailingSMTP.attempts = 0
    _patch_smtp(monkeypatch, FailingSMTP)
    monkeypatch.setattr(email_service.time, "sleep", lambda s: None)
    msg = _make_message()
    with caplog.at_level(logging.ERROR):
        email_service.send_email_via_smtp(email_app, msg)
    assert FailingSMTP.attempts == 3
    queued = tmp_path / "queue.jsonl"
    assert queued.exists()
    data = [json.loads(ln) for ln in queued.read_text().splitlines()]
    assert data[0]["to"] == "user@example.com"
