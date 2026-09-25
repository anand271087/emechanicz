from tests.fakes import make_client


def setup():
    c, db = make_client()
    cid = c.post("/api/v1/customers", json={"company_name": "MaxEye Technologies Pvt. Ltd.",
                                            "contact_person": "Mr.Reegan.M"}).json()["id"]
    return c, db, cid


def payload(cid, ref="ETS/P302/26-27", items=None):
    return {"ref_no": ref, "customer_id": cid, "kind_attn": "Mr.Reegan.M",
            "quote_date": "2026-09-01", "issue_status": "1.1", "terms": ["Net 30"],
            "items": items if items is not None else [
                {"sl_no": 1, "description": "Pneumatic Fixture (1IN1 PCBA)", "qty": 12,
                 "unit_price": 137850}]}


def test_next_ref_suggests_following_number():
    c, _, _ = setup()
    assert c.get("/api/v1/quotes/next-ref").json()["ref_no"].startswith("ETS/P302/")


def test_create_computes_subtotal_and_words():
    c, _, cid = setup()
    r = c.post("/api/v1/quotes", json=payload(cid))
    assert r.status_code == 201
    q = r.json()
    assert q["subtotal"] == 1654200
    assert q["amount_in_words"] == "Sixteen Lakh Fifty Four Thousand Two Hundred Only"
    assert q["status"] == "draft"
    assert q["customers"]["company_name"].startswith("MaxEye")
    assert q["quote_items"][0]["total"] == 1654200


def test_create_with_suggested_ref_bumps_sequence():
    c, _, cid = setup()
    ref = c.get("/api/v1/quotes/next-ref").json()["ref_no"]
    c.post("/api/v1/quotes", json=payload(cid, ref=ref))
    assert c.get("/api/v1/quotes/next-ref").json()["ref_no"] != ref


def test_manual_higher_ref_moves_sequence_forward():
    c, db, cid = setup()
    fy = c.get("/api/v1/quotes/next-ref").json()["ref_no"].split("/")[-1]
    c.post("/api/v1/quotes", json=payload(cid, ref=f"ETS/P350/{fy}"))
    assert c.get("/api/v1/quotes/next-ref").json()["ref_no"] == f"ETS/P351/{fy}"


def test_duplicate_ref_returns_409_with_suggestion():
    c, _, cid = setup()
    c.post("/api/v1/quotes", json=payload(cid))
    r = c.post("/api/v1/quotes", json=payload(cid))
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "already exists" in detail["message"]
    assert detail["suggested_ref"] != "ETS/P302/26-27"


def test_unknown_customer_rejected():
    c, _, _ = setup()
    assert c.post("/api/v1/quotes", json=payload("missing")).status_code == 422


def test_get_quote_items_sorted_and_404():
    c, _, cid = setup()
    items = [{"sl_no": 2, "description": "B", "qty": 1, "unit_price": 1},
             {"sl_no": 1, "description": "A", "qty": 1, "unit_price": 1}]
    qid = c.post("/api/v1/quotes", json=payload(cid, items=items)).json()["id"]
    got = c.get(f"/api/v1/quotes/{qid}").json()
    assert [i["description"] for i in got["quote_items"]] == ["A", "B"]
    assert c.get("/api/v1/quotes/nope").status_code == 404


def test_update_replaces_items_and_recomputes():
    c, db, cid = setup()
    qid = c.post("/api/v1/quotes", json=payload(cid)).json()["id"]
    body = payload(cid, items=[{"sl_no": 1, "description": "Rack", "qty": 1, "unit_price": 75200}])
    r = c.put(f"/api/v1/quotes/{qid}", json=body)
    assert r.status_code == 200
    assert r.json()["subtotal"] == 75200
    assert len(db.tables["quote_items"]) == 1


def test_update_to_other_quotes_ref_409():
    c, _, cid = setup()
    c.post("/api/v1/quotes", json=payload(cid, ref="ETS/P1/26-27"))
    qid = c.post("/api/v1/quotes", json=payload(cid, ref="ETS/P2/26-27")).json()["id"]
    assert c.put(f"/api/v1/quotes/{qid}", json=payload(cid, ref="ETS/P1/26-27")).status_code == 409


def test_list_search_matches_ref_and_customer_and_status():
    c, _, cid = setup()
    c.post("/api/v1/quotes", json=payload(cid, ref="ETS/P1/26-27"))
    assert len(c.get("/api/v1/quotes?search=maxeye").json()) == 1
    assert len(c.get("/api/v1/quotes?search=P1/").json()) == 1
    assert c.get("/api/v1/quotes?search=yale").json() == []
    assert c.get("/api/v1/quotes?status=sent").json() == []


def test_duplicate_creates_new_draft_copy():
    c, _, cid = setup()
    qid = c.post("/api/v1/quotes", json=payload(cid)).json()["id"]
    r = c.post(f"/api/v1/quotes/{qid}/duplicate")
    assert r.status_code == 201
    dup = r.json()
    assert dup["id"] != qid and dup["ref_no"] != "ETS/P302/26-27"
    assert dup["subtotal"] == 1654200 and dup["status"] == "draft"


def test_delete_quote_removes_items():
    c, db, cid = setup()
    qid = c.post("/api/v1/quotes", json=payload(cid)).json()["id"]
    assert c.delete(f"/api/v1/quotes/{qid}").status_code == 204
    assert db.tables["quote_items"] == []


def test_amount_words_endpoint():
    c, _, _ = setup()
    r = c.get("/api/v1/quotes/amount-words?amount=2138000")
    assert r.json() == {"words": "Twenty One Lakh Thirty Eight Thousand Only"}
