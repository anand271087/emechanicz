"""Saved line-item descriptions that feed the quotation builder's description dropdown."""
import logging
from datetime import datetime, timezone

from fastapi import HTTPException

log = logging.getLogger("emechanicz")
TABLE = "item_descriptions"
SEARCH_POOL = 200


def description_key(text: str) -> str:
    """Case- and whitespace-insensitive identity of a description."""
    return " ".join(text.lower().split())


def _like_literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def suggest(db, q: str = "", limit: int = 5) -> list[dict]:
    """Most recently used descriptions containing q; those starting with q come first."""
    key = description_key(q)
    query = db.table(TABLE).select("*").order("last_used_at", desc=True)
    if key:
        query = query.ilike("description_key", f"%{_like_literal(key)}%")
    rows = query.limit(SEARCH_POOL if key else limit).execute().data
    if key:
        rows.sort(key=lambda r: not r["description_key"].startswith(key))  # stable: keeps recency order
    return rows[:limit]


def record(db, descriptions: list[str], touch: bool = True) -> None:
    """Add unseen descriptions; with touch, also mark all of them as just used.

    Never raises: failing to update the suggestion list must not block saving or sending a quote.
    """
    unique: dict[str, str] = {}
    for text in descriptions:
        key = description_key(text or "")
        if key and key not in unique:
            unique[key] = text.strip()
    if not unique:
        return
    now = datetime.now(timezone.utc).isoformat()
    try:
        db.table(TABLE).upsert(
            [{"description": d, "description_key": k, "last_used_at": now} for k, d in unique.items()],
            on_conflict="description_key", ignore_duplicates=True).execute()
        if touch:
            db.table(TABLE).update({"last_used_at": now}).in_("description_key", list(unique)).execute()
    except Exception:
        log.exception("Could not save item descriptions")


def rename(db, did: str, description: str) -> dict:
    key = description_key(description)
    clash = db.table(TABLE).select("id").eq("description_key", key).neq("id", did).execute().data
    if clash:
        raise HTTPException(409, "That description is already in the list")
    rows = db.table(TABLE).update({"description": description.strip(), "description_key": key}
                                  ).eq("id", did).execute().data
    if not rows:
        raise HTTPException(404, "Description not found")
    return rows[0]


def delete(db, did: str) -> None:
    db.table(TABLE).delete().eq("id", did).execute()
