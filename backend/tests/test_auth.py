import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

from app import deps

KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_KEY = ec.generate_private_key(ec.SECP256R1())


def make_token(role="user", key=KEY, exp_offset=600):
    return jwt.encode(
        {"sub": "u1", "email": "a@b.c", "exp": time.time() + exp_offset,
         "aud": "authenticated", "app_metadata": {"role": role}},
        key, algorithm="ES256",
    )


@pytest.fixture(autouse=True)
def fixed_signing_key(monkeypatch):
    monkeypatch.setattr(deps, "_signing_key", lambda token: KEY.public_key())


def test_valid_token_yields_user_with_role():
    user = deps.decode_user(make_token("admin"))
    assert (user.id, user.email, user.role) == ("u1", "a@b.c", "admin")


def test_self_registered_account_without_role_rejected():
    token = jwt.encode({"sub": "u2", "exp": time.time() + 60, "aud": "authenticated"},
                       KEY, algorithm="ES256")
    with pytest.raises(HTTPException) as e:
        deps.decode_user(token)
    assert e.value.status_code == 403


def test_unknown_role_rejected():
    with pytest.raises(HTTPException) as e:
        deps.decode_user(make_token("superuser"))
    assert e.value.status_code == 403


def test_token_signed_by_other_key_rejected():
    with pytest.raises(HTTPException) as e:
        deps.decode_user(make_token(key=OTHER_KEY))
    assert e.value.status_code == 401


def test_expired_token_rejected():
    with pytest.raises(HTTPException) as e:
        deps.decode_user(make_token(exp_offset=-10))
    assert e.value.status_code == 401


def test_missing_bearer_rejected():
    with pytest.raises(HTTPException) as e:
        deps.get_current_user(authorization="")
    assert e.value.status_code == 401


def test_require_admin_blocks_user():
    with pytest.raises(HTTPException) as e:
        deps.require_admin(deps.CurrentUser(id="u1", role="user"))
    assert e.value.status_code == 403
