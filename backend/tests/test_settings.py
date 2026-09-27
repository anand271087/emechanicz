from types import SimpleNamespace
from unittest.mock import MagicMock

from tests.fakes import make_client


def test_any_user_can_read_settings():
    c, _ = make_client(role="user")
    s = c.get("/api/v1/settings").json()
    assert {"company", "quote_seq", "default_terms", "default_intro"} <= set(s)


def test_user_cannot_update_settings():
    c, _ = make_client(role="user")
    assert c.put("/api/v1/settings/company", json={"value": {}}).status_code == 403


def test_admin_updates_known_setting():
    c, _ = make_client(role="admin")
    r = c.put("/api/v1/settings/default_terms", json={"value": ["Net 45"]})
    assert r.status_code == 200
    assert c.get("/api/v1/settings").json()["default_terms"] == ["Net 45"]


def test_unknown_setting_key_rejected():
    c, _ = make_client(role="admin")
    assert c.put("/api/v1/settings/hack", json={"value": 1}).status_code == 404


def test_quote_seq_validated():
    c, _ = make_client(role="admin")
    bad = c.put("/api/v1/settings/quote_seq", json={"value": {"prefix": "P"}})
    assert bad.status_code == 422


def _auth_admin(db):
    admin = MagicMock()
    admin.list_users.return_value = [SimpleNamespace(
        id="u1", email="admin@emechanicz.com", app_metadata={"role": "admin"},
        created_at="2026-09-25", last_sign_in_at=None)]
    admin.create_user.return_value = SimpleNamespace(user=SimpleNamespace(
        id="u2", email="sales@emechanicz.com", app_metadata={"role": "user"},
        created_at="2026-09-25", last_sign_in_at=None))
    db.auth = SimpleNamespace(admin=admin)
    return admin


def test_admin_lists_users():
    c, db = make_client(role="admin")
    _auth_admin(db)
    assert c.get("/api/v1/users").json()[0] == {
        "id": "u1", "email": "admin@emechanicz.com", "name": "", "role": "admin",
        "created_at": "2026-09-25", "last_sign_in_at": None}


def test_admin_creates_user_with_role():
    c, db = make_client(role="admin")
    admin = _auth_admin(db)
    r = c.post("/api/v1/users", json={"email": "sales@emechanicz.com",
                                      "password": "Secret@123", "role": "user"})
    assert r.status_code == 201 and r.json()["email"] == "sales@emechanicz.com"
    sent = admin.create_user.call_args.args[0]
    assert sent["app_metadata"] == {"role": "user"} and sent["email_confirm"] is True


def test_short_password_rejected():
    c, db = make_client(role="admin")
    _auth_admin(db)
    r = c.post("/api/v1/users", json={"email": "a@b.co", "password": "123", "role": "user"})
    assert r.status_code == 422


def test_non_admin_cannot_list_users():
    c, _ = make_client(role="user")
    assert c.get("/api/v1/users").status_code == 403


def test_me_returns_current_user():
    c, _ = make_client(role="admin")
    assert c.get("/api/v1/me").json()["role"] == "admin"


def test_users_have_names_with_email_fallback():
    from tests.fakes import FakeUser
    c, db = make_client(role="admin")
    db.auth.users = [FakeUser("u1", "admin@emechanicz.com", "Admin", "admin"),
                     FakeUser("u2", "sales@emechanicz.com", "")]
    users = {u["email"]: u["name"] for u in c.get("/api/v1/users").json()}
    assert users == {"admin@emechanicz.com": "Admin", "sales@emechanicz.com": ""}


def test_create_user_with_name():
    c, db = make_client(role="admin")
    r = c.post("/api/v1/users", json={"email": "ravi@emechanicz.com", "password": "Secret@123",
                                      "role": "user", "name": "  Ravi Kumar "})
    assert r.status_code == 201 and r.json()["name"] == "Ravi Kumar"
    assert db.auth.users[-1].user_metadata == {"name": "Ravi Kumar"}


def test_admin_renames_member():
    from tests.fakes import FakeUser
    c, db = make_client(role="admin")
    db.auth.users = [FakeUser("u2", "sales@emechanicz.com", "")]
    r = c.put("/api/v1/users/u2", json={"name": "Priya S"})
    assert r.status_code == 200 and r.json()["name"] == "Priya S"


def test_rename_unknown_member_404():
    c, db = make_client(role="admin")
    assert c.put("/api/v1/users/nobody", json={"name": "X"}).status_code == 404


def test_non_admin_cannot_rename():
    c, _ = make_client(role="user")
    assert c.put("/api/v1/users/u1", json={"name": "Me"}).status_code == 403
