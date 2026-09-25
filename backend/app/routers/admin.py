from fastapi import APIRouter, Depends, HTTPException
from pydantic import TypeAdapter, ValidationError

from app.deps import CurrentUser, get_current_user, get_db, require_admin
from app.schemas.settings import SETTING_MODELS, SettingIn, UserIn
from app.services.app_settings import set_setting

router = APIRouter(prefix="/api/v1", tags=["admin"])


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    return user


@router.get("/settings")
def read_settings(db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = db.table("app_settings").select("*").execute().data
    return {r["key"]: r["value"] for r in rows}


@router.put("/settings/{key}")
def update_setting(key: str, body: SettingIn, db=Depends(get_db),
                   admin: CurrentUser = Depends(require_admin)):
    if key not in SETTING_MODELS:
        raise HTTPException(404, f"Unknown setting '{key}'")
    try:
        value = TypeAdapter(SETTING_MODELS[key]).validate_python(body.value)
    except ValidationError as e:
        raise HTTPException(422, e.errors(include_url=False, include_context=False))
    value = value.model_dump() if hasattr(value, "model_dump") else value
    set_setting(db, key, value)
    return {"key": key, "value": value}


def _user_out(u) -> dict:
    return {"id": u.id, "email": u.email, "role": (u.app_metadata or {}).get("role", "user"),
            "created_at": str(u.created_at) if u.created_at else None,
            "last_sign_in_at": str(u.last_sign_in_at) if u.last_sign_in_at else None}


@router.get("/users")
def list_users(db=Depends(get_db), admin: CurrentUser = Depends(require_admin)):
    return [_user_out(u) for u in db.auth.admin.list_users()]


@router.post("/users", status_code=201)
def create_user(body: UserIn, db=Depends(get_db), admin: CurrentUser = Depends(require_admin)):
    try:
        res = db.auth.admin.create_user({"email": body.email, "password": body.password,
                                         "email_confirm": True,
                                         "app_metadata": {"role": body.role}})
    except Exception as e:
        raise HTTPException(400, f"Could not create user: {e}")
    return _user_out(res.user)
