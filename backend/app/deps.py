from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel
from supabase import Client, create_client

from app.config import settings


class CurrentUser(BaseModel):
    id: str
    email: str = ""
    role: str = "user"


@lru_cache
def get_db() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


def _signing_key(token: str):
    return _jwks_client().get_signing_key_from_jwt(token).key


def decode_user(token: str) -> CurrentUser:
    try:
        claims = jwt.decode(token, _signing_key(token), algorithms=["ES256"],
                            audience="authenticated")
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Invalid token: {e}")
    return CurrentUser(
        id=claims["sub"],
        email=claims.get("email", ""),
        role=(claims.get("app_metadata") or {}).get("role", "user"),
    )


def get_current_user(authorization: str = Header("")) -> CurrentUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    return decode_user(authorization.removeprefix("Bearer "))


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    return user
