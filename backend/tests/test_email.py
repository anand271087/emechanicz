import smtplib
from unittest.mock import MagicMock

import pytest

from app.config import settings
from app.services import mailer
from tests.fakes import make_client


@pytest.fixture
def smtp(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "sales@emechanicz.com")
    monkeypatch.setattr(settings, "smtp_password", "pw")
    monkeypatch.setattr(settings, "smtp_from", "sales@emechanicz.com")
    server = MagicMock()
    factory = MagicMock(return_value=server)
    server.__enter__.return_value = server
    monkeypatch.setattr(mailer.smtplib, "SMTP", factory)
    return server


def make_quote():
    c, db = make_client()
    cid = c.post("/api/v1/customers", json={"company_name": "Yale",
                                            "email": "buyer@yale.test"}).json()["id"]
    qid = c.post("/api/v1/quotes", json={
        "ref_no": "ETS/SS10/26-27", "customer_id": cid, "quote_date": "2026-05-23",
        "items": [{"sl_no": 1, "description": "Rack", "qty": 1, "unit_price": 75200}]}).json()["id"]
    return c, db, qid


def body(**kw):
    return {"to": ["buyer@yale.test"], "cc": [], "subject": "Quotation", "body": "Hi", **kw}


def test_email_draft_prefills_customer_and_subject():
    c, _, qid = make_quote()
    d = c.get(f"/api/v1/quotes/{qid}/email-draft").json()
    assert d["to"] == ["buyer@yale.test"]
    assert d["subject"] == "Quotation ETS/SS10/26-27 - Emechanicz Test Solutions"
    assert "ETS/SS10/26-27" in d["body"]


def test_send_attaches_pdf_and_marks_sent(smtp):
    c, db, qid = make_quote()
    r = c.post(f"/api/v1/quotes/{qid}/send-email", json=body(cc=["boss@yale.test"]))
    assert r.status_code == 200 and r.json() == {"sent": True}
    msg = smtp.send_message.call_args.args[0]
    assert msg["To"] == "buyer@yale.test" and msg["Cc"] == "boss@yale.test"
    names = [p.get_filename() for p in msg.iter_attachments()]
    assert names == ["Quote-ETS-SS10-26-27-Yale.pdf"]
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("sales@emechanicz.com", "pw")
    assert c.get(f"/api/v1/quotes/{qid}").json()["status"] == "sent"


def test_send_can_attach_word_too(smtp):
    c, _, qid = make_quote()
    c.post(f"/api/v1/quotes/{qid}/send-email", json=body(attach_docx=True))
    msg = smtp.send_message.call_args.args[0]
    assert [p.get_filename()[-4:] for p in msg.iter_attachments()] == [".pdf", "docx"]


def test_smtp_failure_keeps_draft(smtp):
    smtp.send_message.side_effect = smtplib.SMTPAuthenticationError(535, b"bad creds")
    c, _, qid = make_quote()
    r = c.post(f"/api/v1/quotes/{qid}/send-email", json=body())
    assert r.status_code == 502
    assert "bad creds" in r.json()["detail"]
    assert c.get(f"/api/v1/quotes/{qid}").json()["status"] == "draft"


def test_smtp_not_configured_returns_503(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "")
    c, _, qid = make_quote()
    r = c.post(f"/api/v1/quotes/{qid}/send-email", json=body())
    assert r.status_code == 503 and "not configured" in r.json()["detail"]


def test_invalid_recipient_rejected(smtp):
    c, _, qid = make_quote()
    assert c.post(f"/api/v1/quotes/{qid}/send-email", json=body(to=["nope"])).status_code == 422
    assert c.post(f"/api/v1/quotes/{qid}/send-email", json=body(to=[])).status_code == 422


def test_port_465_uses_ssl(smtp, monkeypatch):
    monkeypatch.setattr(settings, "smtp_port", 465)
    ssl_server = MagicMock()
    ssl_server.__enter__.return_value = ssl_server
    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", MagicMock(return_value=ssl_server))
    c, _, qid = make_quote()
    assert c.post(f"/api/v1/quotes/{qid}/send-email", json=body()).status_code == 200
    ssl_server.send_message.assert_called_once()
