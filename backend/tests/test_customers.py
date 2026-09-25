from fastapi.testclient import TestClient

from app.main import app
from tests.fakes import make_client


def test_requires_login():
    r = TestClient(app).get("/api/v1/customers")
    assert r.status_code == 401


def test_create_and_list():
    c, _ = make_client()
    r = c.post("/api/v1/customers", json={"company_name": "Yale Electronics",
                                          "contact_person": "Mr Jayashekar R"})
    assert r.status_code == 201
    assert r.json()["id"]
    listed = c.get("/api/v1/customers").json()
    assert [x["company_name"] for x in listed] == ["Yale Electronics"]


def test_search_filters_by_name():
    c, _ = make_client()
    c.post("/api/v1/customers", json={"company_name": "Yale Electronics"})
    c.post("/api/v1/customers", json={"company_name": "MaxEye Technologies"})
    names = [x["company_name"] for x in c.get("/api/v1/customers?search=max").json()]
    assert names == ["MaxEye Technologies"]


def test_blank_company_name_rejected():
    c, _ = make_client()
    assert c.post("/api/v1/customers", json={"company_name": "  "}).status_code == 422


def test_update_customer():
    c, _ = make_client()
    cid = c.post("/api/v1/customers", json={"company_name": "Yale"}).json()["id"]
    r = c.put(f"/api/v1/customers/{cid}", json={"company_name": "Yale Ltd", "email": "a@y.com"})
    assert r.status_code == 200 and r.json()["email"] == "a@y.com"


def test_update_missing_customer_404():
    c, _ = make_client()
    assert c.put("/api/v1/customers/nope", json={"company_name": "X"}).status_code == 404


def test_delete_customer_with_quotes_blocked():
    c, db = make_client()
    cid = c.post("/api/v1/customers", json={"company_name": "Yale"}).json()["id"]
    db.tables["quotes"].append({"id": "q1", "customer_id": cid, "ref_no": "R1"})
    assert c.delete(f"/api/v1/customers/{cid}").status_code == 409


def test_delete_customer():
    c, _ = make_client()
    cid = c.post("/api/v1/customers", json={"company_name": "Yale"}).json()["id"]
    assert c.delete(f"/api/v1/customers/{cid}").status_code == 204
    assert c.get("/api/v1/customers").json() == []
