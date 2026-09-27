from datetime import datetime, timedelta, timezone

from app.services.item_descriptions import description_key
from tests.fakes import make_client


def seed(db, *descs):
    start = datetime.now(timezone.utc) - timedelta(days=1)
    for i, d in enumerate(descs):  # later entries are more recently used, all in the past
        db.tables["item_descriptions"].append({
            "id": f"d{i}", "description": d, "description_key": description_key(d),
            "last_used_at": (start + timedelta(seconds=i)).isoformat()})


def suggest(c, q="", limit=5):
    return [d["description"] for d in c.get(f"/api/v1/item-descriptions?q={q}&limit={limit}").json()]


def quote_body(cid, *descs, ref="ETS/P900/26-27"):
    return {"ref_no": ref, "customer_id": cid, "quote_date": "2026-09-27",
            "items": [{"sl_no": i + 1, "description": d} for i, d in enumerate(descs)]}


def new_customer(c):
    return c.post("/api/v1/customers", json={"company_name": "Yale"}).json()["id"]


# --- key normalisation ---

def test_key_is_case_and_whitespace_insensitive():
    assert description_key("  Oscilloscope ") == description_key("oscilloscope")
    assert description_key("DMM  -\t6 1/2\nDigit") == "dmm - 6 1/2 digit"


# --- suggestions ---

def test_empty_query_returns_five_most_recent():
    c, db = make_client()
    seed(db, "A", "B", "C", "D", "E", "F", "G")
    assert suggest(c) == ["G", "F", "E", "D", "C"]


def test_contains_match_is_case_insensitive():
    c, db = make_client()
    seed(db, "32 Channel Relay card", "Oscilloscope", "Relay module")
    assert set(suggest(c, "RELAY")) == {"32 Channel Relay card", "Relay module"}


def test_starts_with_matches_listed_first():
    c, db = make_client()
    seed(db, "Relay module", "32 Channel Relay card")  # contains-match is more recent
    assert suggest(c, "rel") == ["Relay module", "32 Channel Relay card"]


def test_results_capped_at_limit():
    c, db = make_client()
    seed(db, *[f"Fixture {n}" for n in range(9)])
    assert len(suggest(c, "fix")) == 5


def test_wildcard_characters_are_literal():
    c, db = make_client()
    seed(db, "100% tested board", "Plain board")
    assert suggest(c, "100%") == ["100% tested board"]
    assert suggest(c, "_") == []


# --- saving new descriptions ---

def test_saving_quote_adds_new_descriptions_once_case_insensitive():
    c, db = make_client()
    seed(db, "Oscilloscope")
    cid = new_customer(c)
    assert c.post("/api/v1/quotes", json=quote_body(
        cid, "oscilloscope ", "Test Fixture", "TEST FIXTURE")).status_code == 201
    keys = sorted(d["description_key"] for d in db.tables["item_descriptions"])
    assert keys == ["oscilloscope", "test fixture"]
    shown = {d["description_key"]: d["description"] for d in db.tables["item_descriptions"]}
    assert shown["oscilloscope"] == "Oscilloscope"  # first-seen spelling kept


def test_saving_quote_marks_existing_description_recently_used():
    c, db = make_client()
    seed(db, "Old item", "Newer item")
    cid = new_customer(c)
    c.post("/api/v1/quotes", json=quote_body(cid, "old item"))
    assert suggest(c)[0] == "Old item"


def test_updating_quote_adds_descriptions():
    c, db = make_client()
    cid = new_customer(c)
    qid = c.post("/api/v1/quotes", json=quote_body(cid, "First")).json()["id"]
    c.put(f"/api/v1/quotes/{qid}", json=quote_body(cid, "First", "Second"))
    assert set(suggest(c)) == {"First", "Second"}


def _legacy_quote(c, db, desc):
    """A quote whose items were saved before the description list existed."""
    cid = new_customer(c)
    qid = c.post("/api/v1/quotes", json=quote_body(cid, desc)).json()["id"]
    db.tables["item_descriptions"].clear()
    return qid


def test_pdf_download_saves_descriptions():
    c, db = make_client()
    qid = _legacy_quote(c, db, "Legacy rack")
    assert c.get(f"/api/v1/quotes/{qid}/pdf").status_code == 200
    assert suggest(c) == ["Legacy rack"]


def test_docx_download_saves_descriptions():
    c, db = make_client()
    qid = _legacy_quote(c, db, "Legacy rack")
    assert c.get(f"/api/v1/quotes/{qid}/docx").status_code == 200
    assert suggest(c) == ["Legacy rack"]


def test_description_save_failure_does_not_block_quote_save():
    c, db = make_client()
    cid = new_customer(c)
    db.fail_on = lambda q: q.table == "item_descriptions"
    assert c.post("/api/v1/quotes", json=quote_body(cid, "Anything")).status_code == 201


# --- managing the list ---

def test_rename_description():
    c, db = make_client()
    seed(db, "Osciloscope")
    r = c.put("/api/v1/item-descriptions/d0", json={"description": "Oscilloscope"})
    assert r.status_code == 200 and r.json()["description_key"] == "oscilloscope"
    assert suggest(c) == ["Oscilloscope"]


def test_rename_to_existing_description_conflicts():
    c, db = make_client()
    seed(db, "Oscilloscope", "Osciloscope")
    r = c.put("/api/v1/item-descriptions/d1", json={"description": "OSCILLOSCOPE"})
    assert r.status_code == 409


def test_rename_blank_rejected():
    c, db = make_client()
    seed(db, "Rack")
    assert c.put("/api/v1/item-descriptions/d0", json={"description": "  "}).status_code == 422


def test_delete_description():
    c, db = make_client()
    seed(db, "Typo itme", "Rack")
    assert c.delete("/api/v1/item-descriptions/d0").status_code == 204
    assert suggest(c) == ["Rack"]


def test_requires_login():
    from fastapi.testclient import TestClient
    from app.main import app
    assert TestClient(app).get("/api/v1/item-descriptions").status_code == 401
