from datetime import date

import pytest

from app.config import settings
from app.schemas.quote import QuoteItemIn
from app.services.pdf import render_quote_html
from app.services.quote_logic import compute_totals
from tests.fakes import make_client
from tests.sample_data import COMPANY, QUOTE


def set_seq(db, fy, seq, prefix="P"):
    db.tables["app_settings"] = [r for r in db.tables["app_settings"] if r["key"] != "quote_seq"]
    db.tables["app_settings"].append({"key": "quote_seq", "value": {"prefix": prefix, "fy": fy, "seq": seq}})


def seq_state(db):
    return next(r["value"] for r in db.tables["app_settings"] if r["key"] == "quote_seq")


def client_with_customer():
    c, db = make_client()
    cid = c.post("/api/v1/customers", json={"company_name": "Yale"}).json()["id"]
    return c, db, cid


def create(c, cid, ref, on):
    return c.post("/api/v1/quotes", json={"ref_no": ref, "customer_id": cid, "quote_date": on})


# --- ref number follows the quote date, not the server clock ---

def test_next_ref_uses_requested_date_fy():
    c, db, _ = client_with_customer()
    set_seq(db, "26-27", 301)
    assert c.get("/api/v1/quotes/next-ref?date=2027-03-31").json()["ref_no"] == "ETS/P302/26-27"
    assert c.get("/api/v1/quotes/next-ref?date=2027-04-01").json()["ref_no"] == "ETS/P1/27-28"


def test_first_quote_of_new_fy_moves_counter_to_new_fy():
    c, db, cid = client_with_customer()
    set_seq(db, "26-27", 301)
    assert create(c, cid, "ETS/P1/27-28", "2027-04-01").status_code == 201
    assert seq_state(db) == {"prefix": "P", "fy": "27-28", "seq": 1}


def test_backdated_quote_does_not_rewind_counter():
    c, db, cid = client_with_customer()
    set_seq(db, "27-28", 5)
    assert create(c, cid, "ETS/P400/26-27", "2027-03-31").status_code == 201
    assert seq_state(db) == {"prefix": "P", "fy": "27-28", "seq": 5}


def test_older_fy_suggestion_follows_existing_quotes():
    c, db, cid = client_with_customer()
    set_seq(db, "27-28", 5)
    create(c, cid, "ETS/P310/26-27", "2027-03-30")
    assert c.get("/api/v1/quotes/next-ref?date=2027-03-31").json()["ref_no"] == "ETS/P311/26-27"


def test_quote_in_same_fy_advances_counter():
    c, db, cid = client_with_customer()
    set_seq(db, "26-27", 301)
    create(c, cid, "ETS/P302/26-27", "2026-09-25")
    assert seq_state(db)["seq"] == 302


# --- money rounding matches the builder (half-up to paise) ---

def test_row_total_rounds_half_up():
    rows, subtotal = compute_totals([QuoteItemIn(sl_no=1, description="x", qty=2.5, unit_price=0.01)])
    assert rows[0]["total"] == 0.03 and str(subtotal) == "0.03"


# --- document rendering ---

def test_multiline_description_keeps_line_breaks():
    items = [{**QUOTE["quote_items"][0], "description": "Rack\n25U x 600W"}]
    html = render_quote_html({**QUOTE, "quote_items": items}, COMPANY)
    assert "Rack<br>25U x 600W" in html


def test_multiline_description_still_escaped():
    items = [{**QUOTE["quote_items"][0], "description": "<b>x</b>\ny"}]
    html = render_quote_html({**QUOTE, "quote_items": items}, COMPANY)
    assert "&lt;b&gt;x&lt;/b&gt;<br>y" in html


def test_preview_static_url_respects_forwarded_https():
    c, db, cid = client_with_customer()
    qid = create(c, cid, "ETS/P9/26-27", "2026-09-25").json()["id"]
    html = c.get(f"/api/v1/quotes/{qid}/html", headers={"X-Forwarded-Proto": "https"}).text
    assert 'src="https://testserver/static/logo.png"' in html


# --- admin seeding needs an explicit password ---

def test_seed_admin_refuses_without_password(monkeypatch):
    from scripts import seed_admin
    monkeypatch.setattr(settings, "admin_password", "")
    with pytest.raises(SystemExit, match="ADMIN_PASSWORD"):
        seed_admin.main()
