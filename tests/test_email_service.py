import importlib
from unittest.mock import patch

import pytest

import src.services.email_service as email_service


def reload_service(
    monkeypatch,
    reply_to="reply@example.com",
    from_addr="no-reply@example.com",
):
    monkeypatch.setenv("RESEND_FROM", from_addr)
    monkeypatch.setenv("RESEND_REPLY_TO", reply_to)
    monkeypatch.setenv("RESEND_API_KEY", "test")
    importlib.reload(email_service)
    return email_service


def test_address_normalization(monkeypatch):
    svc = reload_service(monkeypatch)
    with patch("src.services.email_service.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "1"}
        svc.send_email(
            "a@example.com",
            "Oi",
            "<p>hi</p>",
            cc="c@example.com",
            bcc=["b@example.com"],
        )
        params = mock_send.call_args[0][0]
        assert params["to"] == ["a@example.com"]  # nosec B101
        assert params["cc"] == ["c@example.com"]  # nosec B101
        assert params["bcc"] == ["b@example.com"]  # nosec B101
        assert params["reply_to"] == "reply@example.com"  # nosec B101


def test_attachments(monkeypatch):
    svc = reload_service(monkeypatch)
    with patch("src.services.email_service.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "1"}
        attachments = [
            {"filename": "man.pdf", "path": "https://ex.com/man.pdf"},
            {"filename": "img.png", "content": "BASE64"},
        ]
        svc.send_email(
            ["a@example.com"],
            "Oi",
            "<p>hi</p>",
            attachments=attachments,
        )
        params = mock_send.call_args[0][0]
        assert params["attachments"] == attachments  # nosec B101


def test_error_propagation(monkeypatch):
    svc = reload_service(monkeypatch)

    class Boom(Exception):
        pass

    with patch(
        "src.services.email_service.resend.Emails.send",
        side_effect=Boom("bad"),
    ):
        with pytest.raises(Boom):
            svc.send_email("a@example.com", "Oi", "<p>hi</p>")
