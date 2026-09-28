"""Bring existing quotations into the system: read files into drafts, then save reviewed drafts."""
import re
from datetime import datetime, time, timezone

from fastapi import HTTPException

from app.deps import CurrentUser
from app.schemas.quote import QuoteIn
from app.schemas.quote_import import ImportSaveIn
from app.services import quotes, users
from app.services.quote_reader import read_quote
from app.services.ref_no import IST

OWNER_SETTING = "import_owner"


def _setting(db, key: str):
    rows = db.table("app_settings").select("value").eq("key", key).execute().data
    return rows[0]["value"] if rows else None


def default_owner(db, fallback_id: str) -> str:
    """The account imported quotations belong to (Ramya), or the uploader if none is set."""
    owner = (_setting(db, OWNER_SETTING) or {}).get("user_id")
    if owner and owner in users.directory(db):
        return owner
    return fallback_id


def customer_key(name: str) -> str:
    """Company identity ignoring case, spacing and punctuation: "Pvt. Ltd." == "pvt ltd"."""
    return " ".join(re.sub(r"[^\w\s]", " ", name.lower()).split())


def find_customer(db, name: str) -> dict | None:
    key = customer_key(name)
    rows = db.table("customers").select("id, company_name, contact_person").execute().data
    return next((c for c in rows if customer_key(c["company_name"] or "") == key), None)


def read_files(db, files: list[tuple[str, bytes]]) -> list[dict]:
    results = []
    for filename, content in files:
        try:
            draft = read_quote(filename, content)
        except ValueError as e:
            results.append({"filename": filename, "draft": None, "error": str(e),
                            "already_imported": False, "customer_id": None})
            continue
        customer = find_customer(db, draft["customer_name"]) if draft["customer_name"] else None
        taken = bool(draft["ref_no"]) and bool(
            db.table("quotes").select("id").eq("ref_no", draft["ref_no"]).execute().data)
        results.append({"filename": filename, "draft": draft, "error": None, "already_imported": taken,
                        "customer_id": customer["id"] if customer else None})
    return results


def save(db, body: ImportSaveIn, user: CurrentUser) -> dict:
    owner = default_owner(db, user.id)
    if body.owner_id and user.role == "admin":
        if body.owner_id not in users.directory(db):
            raise HTTPException(422, "That team member doesn't exist")
        owner = body.owner_id

    customer = find_customer(db, body.customer_name)
    if customer is None:
        customer = db.table("customers").insert({
            "company_name": body.customer_name, "contact_person": body.kind_attn, "email": "",
            "phone": "", "address": "", "gst_no": ""}).execute().data[0]

    quote_in = QuoteIn(ref_no=body.ref_no, customer_id=customer["id"], kind_attn=body.kind_attn,
                       quote_date=body.quote_date, issue_status=body.issue_status or "1.1", intro=body.intro,
                       terms=body.terms, items=body.items)
    # Imported quotations count on the dashboard on the date printed on them.
    created_at = datetime.combine(body.quote_date, time(12, 0), IST).astimezone(timezone.utc).isoformat()
    return quotes.create_quote(db, quote_in, owner, created_at=created_at, status="sent")


def owner_info(db, fallback_id: str) -> dict:
    owner = default_owner(db, fallback_id)
    return {"user_id": owner, "name": users.creator_name(users.directory(db), owner)}
