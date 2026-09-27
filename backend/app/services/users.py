"""Team member names, kept in each Supabase account's user_metadata."""
import logging

log = logging.getLogger("emechanicz")
FORMER_MEMBER = "Former team member"


def member_name(user) -> str:
    return ((getattr(user, "user_metadata", None) or {}).get("name") or "").strip()


def display_name(user) -> str:
    return member_name(user) or user.email or FORMER_MEMBER


def directory(db) -> dict[str, str]:
    """User id -> name to show (name, else email). Empty if the account list can't be read."""
    try:
        return {u.id: display_name(u) for u in db.auth.admin.list_users()}
    except Exception:
        log.exception("Could not load team member names")
        return {}


def creator_name(names: dict[str, str], user_id: str | None) -> str:
    return names.get(user_id or "", FORMER_MEMBER)
