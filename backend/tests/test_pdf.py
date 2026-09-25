import pytest

from app.services.formatting import format_date, inr
from app.services.quote_layout import table_rows
from app.services.pdf import quote_pdf, render_quote_html
from tests.fakes import make_client
from tests.sample_data import COMPANY, QUOTE


def test_inr_indian_grouping():
    assert inr(2138000) == "21,38,000.00"
    assert inr(137850) == "1,37,850.00"
    assert inr(500) == "500.00"
    assert inr(12345678.5) == "1,23,45,678.50"
    assert inr(None) == ""


def test_format_date_dd_mm_yyyy():
    assert format_date("2026-05-23") == "23-05-2026"


def test_table_rows_merge_group_onto_first_row():
    rows = table_rows(QUOTE["quote_items"])
    assert [r["span"] for r in rows] == [1, 1, 2, 0]
    assert rows[2]["total"] == 2102800.0 and rows[2]["qty"] == 1


def test_html_renders_header_fields():
    html = render_quote_html(QUOTE, COMPANY)
    for text in ["ETS/SS10/26-27", "Yale Electronics Services Pvt Ltd", "Mr Jayashekar R Yale",
                 "23-05-2026", "Further to your enquiry", "29AADCE7362F1ZI"]:
        assert text in html


def test_html_money_and_blank_label_rows():
    html = render_quote_html(QUOTE, COMPANY)
    assert "75,200.00" in html and "21,78,000.00" in html
    assert "None" not in html


def test_html_merged_rows_use_rowspan():
    assert 'rowspan="2"' in render_quote_html(QUOTE, COMPANY)


def test_html_multiline_term_and_ordinals():
    html = render_quote_html(QUOTE, COMPANY)
    assert "No.190/3,Kalkere Village" in html
    assert "1<sup>st</sup> Floor" in html


def test_html_escapes_user_text():
    q = {**QUOTE, "kind_attn": "<script>x</script>"}
    assert "<script>x" not in render_quote_html(q, COMPANY)


@pytest.mark.pdf
def test_pdf_bytes():
    assert quote_pdf(QUOTE, COMPANY)[:4] == b"%PDF"


@pytest.mark.pdf
def test_pdf_endpoint_downloads_named_file():
    c, db = make_client()
    cid = c.post("/api/v1/customers", json={"company_name": "Yale"}).json()["id"]
    qid = c.post("/api/v1/quotes", json={
        "ref_no": "ETS/SS10/26-27", "customer_id": cid, "quote_date": "2026-05-23",
        "items": [{"sl_no": 1, "description": "Rack", "qty": 1, "unit_price": 75200}]}).json()["id"]
    r = c.get(f"/api/v1/quotes/{qid}/pdf")
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    assert 'filename="Quote-ETS-SS10-26-27-Yale.pdf"' in r.headers["content-disposition"]


def test_html_endpoint_returns_preview():
    c, db = make_client()
    cid = c.post("/api/v1/customers", json={"company_name": "Yale"}).json()["id"]
    qid = c.post("/api/v1/quotes", json={
        "ref_no": "ETS/SS10/26-27", "customer_id": cid, "quote_date": "2026-05-23"}).json()["id"]
    r = c.get(f"/api/v1/quotes/{qid}/html")
    assert r.status_code == 200 and "ETS/SS10/26-27" in r.text
    assert "/static/logo.png" in r.text
