"""Unit tests for the Google Apps Script email gateway transport."""

import json

from app.services.notification_service import _send_gateway


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        if isinstance(self.payload, str):
            return self.payload.encode("utf-8")
        return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self, payload: dict):
        self.payload = payload
        self.request = None

    def open(self, request, timeout):
        self.request = request
        assert timeout == 15
        return FakeResponse(self.payload)


def test_gateway_requires_configuration(monkeypatch):
    monkeypatch.delenv("EMAIL_GATEWAY_URL", raising=False)
    monkeypatch.delenv("EMAIL_GATEWAY_SECRET", raising=False)

    result = _send_gateway(
        recipients=["student@example.com"],
        subject="Test",
        text_body="Hello",
        html_body="<p>Hello</p>",
    )

    assert result["status"] == "not_configured"
    assert result["sent"] is False
    assert result["recipient_count"] == 1


def test_gateway_handles_no_recipients(monkeypatch):
    monkeypatch.setenv(
        "EMAIL_GATEWAY_URL",
        "https://example.test/exec",
    )
    monkeypatch.setenv(
        "EMAIL_GATEWAY_SECRET",
        "test-secret",
    )

    result = _send_gateway(
        recipients=[],
        subject="Test",
        text_body="Hello",
        html_body="<p>Hello</p>",
    )

    assert result["status"] == "no_recipients"
    assert result["sent"] is False
    assert result["recipient_count"] == 0


def test_gateway_sends_successfully(monkeypatch):
    monkeypatch.setenv(
        "EMAIL_GATEWAY_URL",
        "https://example.test/exec",
    )
    monkeypatch.setenv(
        "EMAIL_GATEWAY_SECRET",
        "test-secret",
    )

    opener = FakeOpener(
        {
            "ok": True,
            "sent": True,
            "recipient_count": 2,
        }
    )

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: opener.open(request, timeout),
    )

    result = _send_gateway(
        recipients=[
            "one@example.com",
            "two@example.com",
        ],
        subject="ProfPilot Test",
        text_body="Test body",
        html_body="<p>Test body</p>",
    )

    assert result["status"] == "sent"
    assert result["sent"] is True
    assert result["recipient_count"] == 2
    assert result["provider"] == "google_apps_script"

    body = json.loads(opener.request.data.decode("utf-8"))
    assert body["secret"] == "test-secret"
    assert body["to"] == [
        "one@example.com",
        "two@example.com",
    ]
    assert body["subject"] == "ProfPilot Test"


def test_gateway_reports_provider_rejection(monkeypatch):
    monkeypatch.setenv(
        "EMAIL_GATEWAY_URL",
        "https://example.test/exec",
    )
    monkeypatch.setenv(
        "EMAIL_GATEWAY_SECRET",
        "test-secret",
    )

    opener = FakeOpener(
        {
            "ok": False,
            "error": "Unauthorized.",
        }
    )

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: opener.open(request, timeout),
    )

    result = _send_gateway(
        recipients=["student@example.com"],
        subject="Test",
        text_body="Hello",
        html_body="<p>Hello</p>",
    )

    assert result["status"] == "provider_error"
    assert result["sent"] is False
    assert "Unauthorized" in result["message"]


def test_gateway_accepts_html_success_marker(monkeypatch):
    monkeypatch.setenv(
        "EMAIL_GATEWAY_URL",
        "https://example.test/exec",
    )
    monkeypatch.setenv(
        "EMAIL_GATEWAY_SECRET",
        "test-secret",
    )

    opener = FakeOpener("PROFPILOT_OK\\n{\\"ok\\":true}")
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: opener.open(request, timeout),
    )

    result = _send_gateway(
        recipients=["student@example.com"],
        subject="Test",
        text_body="Hello",
        html_body="<p>Hello</p>",
    )

    assert result["status"] == "sent"
    assert result["sent"] is True
    assert result["recipient_count"] == 1


def test_gateway_reports_html_error_marker(monkeypatch):
    monkeypatch.setenv(
        "EMAIL_GATEWAY_URL",
        "https://example.test/exec",
    )
    monkeypatch.setenv(
        "EMAIL_GATEWAY_SECRET",
        "test-secret",
    )

    opener = FakeOpener("PROFPILOT_ERROR\\nUnauthorized.")
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: opener.open(request, timeout),
    )

    result = _send_gateway(
        recipients=["student@example.com"],
        subject="Test",
        text_body="Hello",
        html_body="<p>Hello</p>",
    )

    assert result["status"] == "provider_error"
    assert result["sent"] is False
    assert "PROFPILOT_ERROR" in result["message"]
