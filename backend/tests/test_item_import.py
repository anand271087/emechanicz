import io

from openpyxl import Workbook

from app.services.item_descriptions import capitalize_first
from tests.fakes import make_client
from tests.test_item_descriptions import new_customer, quote_body, seed, suggest

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def xlsx(rows):
    wb = Workbook()
    for r in rows:
        wb.active.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def upload(c, content, name="items.xlsx"):
    return c.post("/api/v1/item-descriptions/import", files={"file": (name, content, XLSX)})


def listed(db):
    return sorted(d["description"] for d in db.tables["item_descriptions"])


# --- first letter capital ---

def test_capitalize_first_changes_only_first_character():
    assert capitalize_first("  oscilloscope ") == "Oscilloscope"
    assert capitalize_first("dMM - 6 1/2 digit") == "DMM - 6 1/2 digit"
    assert capitalize_first("32 channel relay") == "32 channel relay"
    assert capitalize_first("") == ""


def test_quote_line_saved_with_first_letter_capital():
    c, db = make_client()
    cid = new_customer(c)
    q = c.post("/api/v1/quotes", json=quote_body(cid, "test fixture wiring")).json()
    assert q["quote_items"][0]["description"] == "Test fixture wiring"
    assert listed(db) == ["Test fixture wiring"]


def test_full_caps_and_lower_case_are_one_item():
    c, db = make_client()
    cid = new_customer(c)
    c.post("/api/v1/quotes", json=quote_body(cid, "oscilloscope", "OSCILLOSCOPE", ref="ETS/P1/26-27"))
    c.post("/api/v1/quotes", json=quote_body(cid, "Oscilloscope ", ref="ETS/P2/26-27"))
    assert listed(db) == ["Oscilloscope"]


def test_rename_capitalizes():
    c, db = make_client()
    seed(db, "Rack")
    assert c.put("/api/v1/item-descriptions/d0", json={"description": "rack 25u"}).json()["description"] == "Rack 25u"


# --- add one item ---

def test_add_item_capitalized():
    c, db = make_client()
    r = c.post("/api/v1/item-descriptions", json={"description": "  power supply 4ch "})
    assert r.status_code == 201 and r.json()["description"] == "Power supply 4ch"


def test_add_existing_item_in_other_case_conflicts():
    c, db = make_client()
    seed(db, "Oscilloscope")
    r = c.post("/api/v1/item-descriptions", json={"description": "OSCILLOSCOPE"})
    assert r.status_code == 409 and "already" in r.json()["detail"]
    assert listed(db) == ["Oscilloscope"]


def test_added_item_does_not_push_used_items_out_of_recent_five():
    c, db = make_client()
    seed(db, "A", "B", "C", "D", "E")
    c.post("/api/v1/item-descriptions", json={"description": "Brand new"})
    assert "Brand new" not in suggest(c)
    assert suggest(c, "brand") == ["Brand new"]


# --- Excel upload ---

def test_upload_appends_new_and_skips_existing_duplicates_and_blanks():
    c, db = make_client()
    seed(db, "Oscilloscope")
    r = upload(c, xlsx([["Description"], ["OSCILLOSCOPE"], ["dmm - 6 1/2 digit"], [None], ["   "],
                        ["Relay card"], ["relay CARD"]]))
    assert r.status_code == 200
    assert r.json() == {"added": 2, "already_in_list": 1, "repeated_in_file": 1, "blank_rows": 2}
    assert listed(db) == ["Dmm - 6 1/2 digit", "Oscilloscope", "Relay card"]


def test_upload_uses_description_column_when_headed():
    c, db = make_client()
    upload(c, xlsx([["Sl.No.", "Description", "Qty"], [1, "Rack 25U", 2], [2, "Fan", 1]]))
    assert listed(db) == ["Fan", "Rack 25U"]


def test_upload_without_header_uses_first_column_including_first_row():
    c, db = make_client()
    upload(c, xlsx([["Rack 25U", "ignored"], ["Fan", "ignored"]]))
    assert listed(db) == ["Fan", "Rack 25U"]


def test_upload_twice_adds_nothing_the_second_time():
    c, db = make_client()
    content = xlsx([["Description"], ["Rack"], ["Fan"]])
    upload(c, content)
    assert upload(c, content).json()["added"] == 0
    assert listed(db) == ["Fan", "Rack"]


def test_upload_numbers_are_read_as_text():
    c, db = make_client()
    upload(c, xlsx([["Description"], [12345]]))
    assert listed(db) == ["12345"]


def test_upload_rejects_non_excel_file():
    c, _ = make_client()
    r = upload(c, b"not a spreadsheet", name="items.csv")
    assert r.status_code == 400 and "Excel" in r.json()["detail"]


def test_upload_rejects_corrupt_xlsx():
    c, _ = make_client()
    r = upload(c, b"PK\x03\x04 broken", name="items.xlsx")
    assert r.status_code == 400 and "Excel" in r.json()["detail"]


def test_upload_rejects_empty_sheet():
    c, _ = make_client()
    r = upload(c, xlsx([["Description"]]))
    assert r.status_code == 400 and "No descriptions" in r.json()["detail"]
