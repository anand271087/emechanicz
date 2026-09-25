"""Quote persistence and ref-number sequencing."""
import re
from datetime import date, datetime, timezone

from fastapi import HTTPException

from app.schemas.quote import QuoteIn, QuoteItemIn
from app.services.amount_words import amount_in_words
from app.services.app_settings import get_setting, set_setting
from app.services.quote_logic import compute_totals
from app.services.ref_no import next_ref_state

QUOTE_SELECT = "*, customers(*), quote_items(*)"


def _ref_taken(db, ref_no: str, exclude_id: str | None = None) -> bool:
    q = db.table("quotes").select("id").eq("ref_no", ref_no)
    if exclude_id:
        q = q.neq("id", exclude_id)
    return bool(q.execute().data)


def suggest_ref(db) -> str:
    state = get_setting(db, "quote_seq")
    ref, state = next_ref_state(state, date.today())
    while _ref_taken(db, ref):
        ref, state = next_ref_state(state, date.today())
    return ref


def _advance_sequence(db, ref_no: str) -> None:
    """Move the counter past ref_no if it follows the current prefix/FY pattern."""
    state = get_setting(db, "quote_seq")
    _, current = next_ref_state(state, date.today())
    m = re.fullmatch(rf"ETS/{re.escape(current['prefix'])}(\d+)/{re.escape(current['fy'])}", ref_no)
    if not m:
        return
    seq = int(m.group(1))
    base = state["seq"] if state.get("fy") == current["fy"] else 0
    if seq > base:
        set_setting(db, "quote_seq", {**current, "seq": seq})


def fetch_quote(db, qid: str) -> dict:
    rows = db.table("quotes").select(QUOTE_SELECT).eq("id", qid).execute().data
    if not rows:
        raise HTTPException(404, "Quote not found")
    quote = rows[0]
    quote["quote_items"].sort(key=lambda i: i["sl_no"])
    return quote


def list_quotes(db, search: str = "", status: str = "") -> list[dict]:
    q = db.table("quotes").select("*, customers(company_name)").order("created_at", desc=True)
    if status:
        q = q.eq("status", status)
    rows = q.limit(500).execute().data
    if search:
        s = search.lower()
        rows = [r for r in rows if s in r["ref_no"].lower()
                or s in ((r.get("customers") or {}).get("company_name") or "").lower()]
    return rows


def _row(body: QuoteIn, subtotal) -> dict:
    return {
        "ref_no": body.ref_no, "customer_id": body.customer_id, "kind_attn": body.kind_attn,
        "quote_date": body.quote_date.isoformat(), "issue_status": body.issue_status,
        "intro": body.intro, "terms": body.terms, "subtotal": float(subtotal),
        "amount_in_words": amount_in_words(subtotal),
    }


def _check_customer(db, customer_id: str) -> None:
    if not db.table("customers").select("id").eq("id", customer_id).execute().data:
        raise HTTPException(422, "Customer not found")


def _replace_items(db, qid: str, items: list[dict]) -> None:
    db.table("quote_items").delete().eq("quote_id", qid).execute()
    if items:
        db.table("quote_items").insert([{**it, "quote_id": qid} for it in items]).execute()


def _conflict(db, ref_no: str):
    return HTTPException(409, detail={"message": f"Ref no {ref_no} already exists",
                                      "suggested_ref": suggest_ref(db)})


def create_quote(db, body: QuoteIn, user_id: str) -> dict:
    _check_customer(db, body.customer_id)
    if _ref_taken(db, body.ref_no):
        raise _conflict(db, body.ref_no)
    items, subtotal = compute_totals(body.items)
    try:
        quote = db.table("quotes").insert(
            {**_row(body, subtotal), "status": "draft", "created_by": user_id}).execute().data[0]
    except Exception as e:  # unique violation from a concurrent insert
        if "23505" in str(e) or "duplicate key" in str(e):
            raise _conflict(db, body.ref_no)
        raise
    _replace_items(db, quote["id"], items)
    _advance_sequence(db, body.ref_no)
    return fetch_quote(db, quote["id"])


def update_quote(db, qid: str, body: QuoteIn) -> dict:
    fetch_quote(db, qid)
    _check_customer(db, body.customer_id)
    if _ref_taken(db, body.ref_no, exclude_id=qid):
        raise _conflict(db, body.ref_no)
    items, subtotal = compute_totals(body.items)
    db.table("quotes").update({**_row(body, subtotal),
                               "updated_at": datetime.now(timezone.utc).isoformat()}
                              ).eq("id", qid).execute()
    _replace_items(db, qid, items)
    _advance_sequence(db, body.ref_no)
    return fetch_quote(db, qid)


def duplicate_quote(db, qid: str, user_id: str) -> dict:
    src = fetch_quote(db, qid)
    body = QuoteIn(
        ref_no=suggest_ref(db), customer_id=src["customer_id"], kind_attn=src.get("kind_attn", ""),
        quote_date=date.today(), issue_status="1.1", intro=src.get("intro", ""),
        terms=src["terms"],
        items=[QuoteItemIn(**{k: i[k] for k in ("sl_no", "description", "qty", "unit_price", "group_id")})
               for i in src["quote_items"]],
    )
    return create_quote(db, body, user_id)


def delete_quote(db, qid: str) -> None:
    fetch_quote(db, qid)
    db.table("quotes").delete().eq("id", qid).execute()


def mark_sent(db, qid: str) -> None:
    db.table("quotes").update({"status": "sent"}).eq("id", qid).execute()
