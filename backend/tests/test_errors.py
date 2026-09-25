from fastapi.testclient import TestClient

from app.main import app
from app.services.formatting import download_name
from tests.fakes import make_client


def test_unexpected_error_returns_json_with_cors_headers():
    c, db = make_client(role="admin")
    db.fail_on = lambda q: True
    r = TestClient(app, raise_server_exceptions=False).get(
        "/api/v1/customers", headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 500
    assert r.json() == {"detail": "Something went wrong on the server. Try again, or contact your admin."}
    assert r.headers.get("access-control-allow-origin") in ("*", "http://localhost:5173")


def test_download_name_has_no_double_dot():
    q = {"ref_no": "ETS/P302/26-27", "customers": {"company_name": "MaxEye Technologies Pvt. Ltd."}}
    assert download_name(q, "pdf") == "Quote-ETS-P302-26-27-MaxEye Technologies Pvt. Ltd.pdf"
