"""Saved line-item descriptions that feed the quotation builder's description dropdown."""
import logging
from datetime import datetime, timezone

from fastapi import HTTPException

log = logging.getLogger("emechanicz")
TABLE = "item_descriptions"
SEARCH_POOL = 200
IMPORT_CHUNK = 500
# Added/imported items that no quote has used yet: sorted after used ones in "recent" suggestions.
NEVER_USED = "2000-01-01T00:00:00+00:00"


def description_key(text: str) -> str:
    """Case- and whitespace-insensitive identity of a description."""
    return " ".join(text.lower().split())


def capitalize_first(text: str) -> str:
    """Trimmed text with its first character upper-cased; the rest is kept as typed."""
    text = text.strip()
    return text[:1].upper() + text[1:]


def _like_literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def suggest(db, q: str = "", limit: int = 5, sort: str = "recent") -> list[dict]:
    """Descriptions containing q.

    sort="recent": most recently used first, with those starting with q ahead (the dropdown).
    sort="name": alphabetical (the Items page).
    """
    key = description_key(q)
    by_name = sort == "name"
    query = db.table(TABLE).select("*").order("description_key" if by_name else "last_used_at", desc=not by_name)
    if key:
        query = query.ilike("description_key", f"%{_like_literal(key)}%")
    if by_name:
        return query.limit(limit).execute().data
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
            unique[key] = capitalize_first(text)
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


def add(db, description: str) -> dict:
    key = description_key(description)
    if db.table(TABLE).select("id").eq("description_key", key).execute().data:
        raise HTTPException(409, "That description is already in the list")
    return db.table(TABLE).insert({"description": capitalize_first(description), "description_key": key,
                                   "last_used_at": NEVER_USED}).execute().data[0]


def import_descriptions(db, texts: list[str], blank_rows: int = 0) -> dict:
    """Append descriptions, skipping ones already in the list and repeats within the upload."""
    unique: dict[str, str] = {}
    for text in texts:
        unique.setdefault(description_key(text), capitalize_first(text))
    rows = [{"description": d, "description_key": k, "last_used_at": NEVER_USED} for k, d in unique.items()]
    added = 0
    for start in range(0, len(rows), IMPORT_CHUNK):
        inserted = db.table(TABLE).upsert(rows[start:start + IMPORT_CHUNK], on_conflict="description_key",
                                          ignore_duplicates=True).execute().data
        added += len(inserted)
    return {"added": added, "already_in_list": len(unique) - added,
            "repeated_in_file": len(texts) - len(unique), "blank_rows": blank_rows}


def rename(db, did: str, description: str) -> dict:
    key = description_key(description)
    clash = db.table(TABLE).select("id").eq("description_key", key).neq("id", did).execute().data
    if clash:
        raise HTTPException(409, "That description is already in the list")
    rows = db.table(TABLE).update({"description": capitalize_first(description), "description_key": key}
                                  ).eq("id", did).execute().data
    if not rows:
        raise HTTPException(404, "Description not found")
    return rows[0]


def delete(db, did: str) -> None:
    db.table(TABLE).delete().eq("id", did).execute()
