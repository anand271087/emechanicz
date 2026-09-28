from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from tests.fakes import FakeUser, make_client
from tests.test_quote_reader import maxeye_xlsx, yale_xlsx

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
IST = timezone(timedelta(hours=5, minutes=30))


def client(role="admin"):
    c, db = make_client(role=role)
    db.auth.users = [FakeUser("u1", "admin@emechanicz.com", "Admin", "admin"),
                     FakeUser("u-ramya", "ramya@emechanicz.com", "Ramya", "admin"),
                     FakeUser("u-ravi", "ravi@emechanicz.com", "Ravi")]
    db.tables["app_settings"].append({"key": "import_owner", "value": {"user_id": "u-ramya"}})
    return c, db


def read(c, *files):
    r = c.post("/api/v1/quotes/import/read", files=[("files", (n, b, XLSX)) for n, b in files])
    assert r.status_code == 200, r.text
    return r.json()


def draft_body(**over):
    body = {"customer_name": "Yale Electronics Services Pvt Ltd", "kind_attn": "Mr J", "ref_no": "ETS/SS10/26-27",
            "quote_date": "2026-05-23", "issue_status": "1.1", "intro": "", "terms": ["Net 30"],
            "items": [{"sl_no": 1, "description": "rack", "qty": 1, "unit_price": 75200, "group_id": None}]}
    return {**body, **over}


# --- reading ---

def test_read_several_files_returns_a_draft_each():
    c, _ = client()
    res = read(c, ("yale.xlsx", yale_xlsx()), ("maxeye.xlsx", maxeye_xlsx()))
    assert [r["filename"] for r in res] == ["yale.xlsx", "maxeye.xlsx"]
    assert res[0]["draft"]["ref_no"] == "ETS/SS10/26-27" and res[0]["error"] is None
    assert res[1]["draft"]["customer_name"] == "MaxEye Technologies Pvt. Ltd."


def test_read_flags_existing_ref_and_matches_customer_case_insensitively():
    c, db = client()
    db.tables["customers"].append({"id": "c9", "company_name": "YALE ELECTRONICS SERVICES PVT LTD"})
    db.tables["quotes"].append({"id": "q9", "ref_no": "ETS/SS10/26-27", "customer_id": "c9"})
    r = read(c, ("yale.xlsx", yale_xlsx()))[0]
    assert r["already_imported"] is True
    assert r["customer_id"] == "c9"


def test_read_bad_file_reports_error_but_keeps_others():
    c, _ = client()
    res = read(c, ("notes.txt", b"hello"), ("yale.xlsx", yale_xlsx()))
    assert res[0]["draft"] is None and "PDF, Excel" in res[0]["error"]
    assert res[1]["draft"] is not None


def test_read_does_not_save_anything():
    c, db = client()
    read(c, ("yale.xlsx", yale_xlsx()))
    assert db.tables["quotes"] == [] and db.tables["customers"] == []


def test_read_needs_login():
    assert TestClient(app).post("/api/v1/quotes/import/read").status_code == 401


# --- saving ---

def test_save_creates_customer_quote_owned_by_ramya_dated_as_printed():
    c, db = client()
    r = c.post("/api/v1/quotes/import/save", json=draft_body())
    assert r.status_code == 201, r.text
    q = db.tables["quotes"][0]
    assert q["created_by"] == "u-ramya"
    created = datetime.fromisoformat(q["created_at"]).astimezone(IST)
    assert created.date() == date(2026, 5, 23)
    assert db.tables["customers"][0]["company_name"] == "Yale Electronics Services Pvt Ltd"
    assert db.tables["customers"][0]["contact_person"] == "Mr J"
    assert r.json()["quote_items"][0]["description"] == "Rack"
    assert [d["description"] for d in db.tables["item_descriptions"]] == ["Rack"]


def test_save_reuses_existing_customer_ignoring_case():
    c, db = client()
    db.tables["customers"].append({"id": "c9", "company_name": "yale electronics services pvt ltd"})
    c.post("/api/v1/quotes/import/save", json=draft_body())
    assert len(db.tables["customers"]) == 1 and db.tables["quotes"][0]["customer_id"] == "c9"


def test_save_duplicate_ref_rejected():
    c, db = client()
    c.post("/api/v1/quotes/import/save", json=draft_body())
    r = c.post("/api/v1/quotes/import/save", json=draft_body())
    assert r.status_code == 409 and len(db.tables["quotes"]) == 1


def test_admin_can_choose_another_owner():
    c, db = client()
    c.post("/api/v1/quotes/import/save", json=draft_body(owner_id="u-ravi"))
    assert db.tables["quotes"][0]["created_by"] == "u-ravi"


def test_unknown_owner_rejected():
    c, _ = client()
    assert c.post("/api/v1/quotes/import/save", json=draft_body(owner_id="nobody")).status_code == 422


def test_sales_member_import_always_goes_to_ramya():
    c, db = client(role="user")
    c.post("/api/v1/quotes/import/save", json=draft_body(owner_id="u-ravi"))
    assert db.tables["quotes"][0]["created_by"] == "u-ramya"


def test_without_owner_setting_falls_back_to_uploader():
    c, db = client()
    db.tables["app_settings"] = [s for s in db.tables["app_settings"] if s["key"] != "import_owner"]
    c.post("/api/v1/quotes/import/save", json=draft_body())
    assert db.tables["quotes"][0]["created_by"] == "u1"


def test_imported_quote_counts_on_dashboard_by_printed_date(monkeypatch):
    c, db = client()
    monkeypatch.setattr("app.services.dashboard.today_ist", lambda: date(2026, 9, 28))
    c.post("/api/v1/quotes/import/save", json=draft_body(quote_date="2026-05-23"))
    assert c.get("/api/v1/dashboard?period=today").json()["totals"]["quotations"] == 0
    people = c.get("/api/v1/dashboard?period=year").json()["by_person"]
    assert [(p["name"], p["quotations"]) for p in people] == [("Ramya", 1)]
    months = {m["label"]: m["quotations"] for m in c.get("/api/v1/dashboard?period=year").json()["monthly"]}
    assert months["May"] == 1


def test_import_owner_endpoint_names_the_default_owner():
    c, _ = client()
    assert c.get("/api/v1/quotes/import/owner").json() == {"user_id": "u-ramya", "name": "Ramya"}


def test_save_requires_customer_name():
    c, _ = client()
    assert c.post("/api/v1/quotes/import/save", json=draft_body(customer_name=" ")).status_code == 422


def test_customer_match_ignores_punctuation_and_spacing():
    c, db = client()
    db.tables["customers"].append({"id": "c2", "company_name": "MaxEye Technologies Pvt. Ltd"})
    r = read(c, ("maxeye.xlsx", maxeye_xlsx()))[0]  # file says "MaxEye Technologies Pvt. Ltd."
    assert r["customer_id"] == "c2"
    c.post("/api/v1/quotes/import/save", json=draft_body(customer_name="Maxeye Technologies Pvt Ltd.", ref_no="R-1"))
    assert len(db.tables["customers"]) == 1 and db.tables["quotes"][0]["customer_id"] == "c2"
