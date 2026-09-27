"""Admin dashboard: who created how many quotations, for a period of the Indian financial year."""
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

from app.services.ref_no import IST, financial_year, today_ist
from app.services.users import creator_name, directory

Period = Literal["today", "30d", "quarter", "year"]
PAGE = 1000
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _fy_start(d: date) -> date:
    return date(d.year if d.month >= 4 else d.year - 1, 4, 1)


def _quarter_start(d: date) -> date:
    return date(d.year, ((d.month - 1) // 3) * 3 + 1, 1)  # Jan/Apr/Jul/Oct = FY Q4/Q1/Q2/Q3


def period_range(period: str, today: date) -> tuple[date, date]:
    start = {"today": today, "30d": today - timedelta(days=29),
             "quarter": _quarter_start(today), "year": _fy_start(today)}[period]
    return start, today


def _fmt(d: date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def _label(period: str, start: date, end: date) -> str:
    span = f"{_fmt(start)} – {_fmt(end)}"
    if period == "today":
        return f"Today ({_fmt(end)})"
    if period == "30d":
        return f"Last 30 days ({span})"
    fy = financial_year(end)
    if period == "quarter":
        return f"Q{(start.month - 4) % 12 // 3 + 1} FY {fy} ({span})"
    return f"FY {fy} ({span})"


def _created_ist(row: dict) -> datetime:
    return datetime.fromisoformat(row["created_at"]).astimezone(IST)


def _quotes_since(db, start: date) -> list[dict]:
    since = datetime.combine(start, time.min, IST).astimezone(timezone.utc).isoformat()
    rows, offset = [], 0
    while True:
        page = (db.table("quotes")
                .select("id, ref_no, subtotal, created_by, created_at, customers(company_name)")
                .gte("created_at", since).order("created_at", desc=True)
                .range(offset, offset + PAGE - 1).execute().data)
        rows += page
        if len(page) < PAGE:
            return rows
        offset += PAGE


def _money(v) -> float:
    return round(float(v or 0), 2)


def build(db, period: str) -> dict:
    start, end = period_range(period, today_ist())
    quotes = [q for q in _quotes_since(db, start) if start <= _created_ist(q).date() <= end]
    names = directory(db)

    def brief(q: dict) -> dict:
        return {"id": q["id"], "ref_no": q["ref_no"],
                "customer": (q.get("customers") or {}).get("company_name", ""),
                "created_at": q["created_at"], "value": _money(q["subtotal"]),
                "created_by_name": creator_name(names, q.get("created_by"))}

    people: dict[str, list[dict]] = defaultdict(list)
    customers: dict[str, list[float]] = defaultdict(list)
    for q in quotes:
        people[q.get("created_by") or ""].append(q)
        customers[(q.get("customers") or {}).get("company_name") or "Unknown customer"].append(_money(q["subtotal"]))

    by_person = sorted(
        ({"user_id": uid, "name": creator_name(names, uid), "quotations": len(qs),
          "value": _money(sum(_money(q["subtotal"]) for q in qs)),
          "quotes": [brief(q) for q in sorted(qs, key=lambda q: q["created_at"], reverse=True)]}
         for uid, qs in people.items()),
        key=lambda p: (-p["quotations"], -p["value"], p["name"].lower()))

    top_customers = sorted(({"name": n, "quotations": len(v), "value": _money(sum(v))} for n, v in customers.items()),
                           key=lambda c: (-c["value"], c["name"].lower()))[:5]

    monthly = []
    if period == "year":
        counts: dict[tuple[int, int], list[float]] = defaultdict(list)
        for q in quotes:
            d = _created_ist(q)
            counts[(d.year, d.month)].append(_money(q["subtotal"]))
        y, m = start.year, start.month
        while (y, m) <= (end.year, end.month):
            vals = counts.get((y, m), [])
            monthly.append({"month": f"{y}-{m:02d}", "label": MONTHS[m - 1],
                            "quotations": len(vals), "value": _money(sum(vals))})
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)

    total = _money(sum(_money(q["subtotal"]) for q in quotes))
    return {
        "period": period, "label": _label(period, start, end),
        "start": start.isoformat(), "end": end.isoformat(),
        "totals": {"quotations": len(quotes), "value": total,
                   "average": _money(total / len(quotes)) if quotes else 0},
        "by_person": by_person,
        "top_customers": top_customers,
        "recent": [brief(q) for q in sorted(quotes, key=lambda q: q["created_at"], reverse=True)[:10]],
        "monthly": monthly,
    }
