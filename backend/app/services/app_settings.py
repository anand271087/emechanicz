from fastapi import HTTPException


def get_setting(db, key: str):
    rows = db.table("app_settings").select("value").eq("key", key).execute().data
    if not rows:
        raise HTTPException(500, f"Setting '{key}' missing — run the database migration")
    return rows[0]["value"]


def set_setting(db, key: str, value) -> None:
    db.table("app_settings").update({"value": value}).eq("key", key).execute()
