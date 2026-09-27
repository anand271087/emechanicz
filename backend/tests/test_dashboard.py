from datetime import date, datetime, timedelta, timezone

import pytest

from app.services.dashboard import period_range
from tests.fakes import FakeUser, make_client

IST = timezone(timedelta(hours=5, minutes=30))
TODAY = date(2026, 9, 27)


@pytest.mark.parametrize("period,today,expected", [
    ("today", TODAY, (TODAY, TODAY)),
    ("30d", TODAY, (date(2026, 8, 29), TODAY)),
    ("quarter", date(2026, 9, 27), (date(2026, 7, 1), date(2026, 9, 27))),   # Q2: Jul–Sep
    ("quarter", date(2026, 5, 3), (date(2026, 4, 1), date(2026, 5, 3))),     # Q1: Apr–Jun
    ("quarter", date(2027, 1, 15), (date(2027, 1, 1), date(2027, 1, 15))),   # Q4: Jan–Mar
    ("year", date(2027, 2, 10), (date(2026, 4, 1), date(2027, 2, 10))),      # FY starts 1 April
    ("year", date(2026, 4, 1), (date(2026, 4, 1), date(2026, 4, 1))),
])
def test_period_range_uses_financial_year(period, today, expected):
    assert period_range(period, today) == expected


def ist(y, m, d, h=10):
    """An IST wall-clock time, stored as UTC like Postgres timestamptz."""
    return datetime(y, m, d, h, tzinfo=IST).astimezone(timezone.utc).isoformat()


def setup(monkeypatch, quotes):
    monkeypatch.setattr("app.services.dashboard.today_ist", lambda: TODAY)
    c, db = make_client(role="admin")
    db.auth.users = [FakeUser("u-admin", "admin@emechanicz.com", "Admin", "admin"),
                     FakeUser("u-ravi", "ravi@emechanicz.com", "Ravi Kumar"),
                     FakeUser("u-noname", "priya@emechanicz.com", "")]
    db.tables["customers"] = [{"id": "c1", "company_name": "Yale Electronics"},
                              {"id": "c2", "company_name": "MaxEye Technologies"}]
    for n, (who, cust, value, created) in enumerate(quotes, start=1):
        db.tables["quotes"].append({"id": f"q{n}", "ref_no": f"ETS/P{n}/26-27", "customer_id": cust,
                                    "subtotal": value, "created_by": who, "created_at": created,
                                    "quote_date": created[:10], "status": "draft"})
    return c, db


def dash(c, period):
    r = c.get(f"/api/v1/dashboard?period={period}")
    assert r.status_code == 200, r.text
    return r.json()


QUOTES = [
    ("u-ravi", "c1", 100000, ist(2026, 9, 27)),          # today
    ("u-ravi", "c2", 50000, ist(2026, 9, 20)),           # this month
    ("u-admin", "c1", 200000, ist(2026, 9, 27, 0)),      # today 00:xx IST = yesterday in UTC
    ("u-noname", "c2", 10000, ist(2026, 7, 2)),          # this quarter, not last 30 days
    ("u-ravi", "c1", 30000, ist(2026, 4, 5)),            # this FY, not this quarter
    ("u-admin", "c1", 999999, ist(2026, 3, 31, 23)),     # previous FY
]


def test_today_counts_by_india_date(monkeypatch):
    c, _ = setup(monkeypatch, QUOTES)
    d = dash(c, "today")
    assert d["totals"] == {"quotations": 2, "value": 300000, "average": 150000}
    assert {p["name"]: p["quotations"] for p in d["by_person"]} == {"Admin": 1, "Ravi Kumar": 1}


def test_periods_include_the_right_quotes(monkeypatch):
    c, _ = setup(monkeypatch, QUOTES)
    assert dash(c, "30d")["totals"]["quotations"] == 3
    assert dash(c, "quarter")["totals"]["quotations"] == 4
    assert dash(c, "year")["totals"]["quotations"] == 5


def test_by_person_sorted_with_their_quotes(monkeypatch):
    c, _ = setup(monkeypatch, QUOTES)
    people = dash(c, "year")["by_person"]
    assert [(p["name"], p["quotations"], p["value"]) for p in people] == [
        ("Ravi Kumar", 3, 180000), ("Admin", 1, 200000), ("priya@emechanicz.com", 1, 10000)]
    assert [q["ref_no"] for q in people[0]["quotes"]] == ["ETS/P1/26-27", "ETS/P2/26-27", "ETS/P5/26-27"]
    assert people[0]["quotes"][0]["customer"] == "Yale Electronics"


def test_deleted_member_still_counted(monkeypatch):
    c, _ = setup(monkeypatch, [("u-gone", "c1", 5000, ist(2026, 9, 27))])
    assert dash(c, "today")["by_person"][0]["name"] == "Former team member"


def test_top_customers_by_value(monkeypatch):
    c, _ = setup(monkeypatch, QUOTES)
    top = dash(c, "year")["top_customers"]
    assert top == [{"name": "Yale Electronics", "quotations": 3, "value": 330000},
                   {"name": "MaxEye Technologies", "quotations": 2, "value": 60000}]


def test_recent_lists_latest_ten_with_creator(monkeypatch):
    many = [("u-ravi", "c1", 1000, ist(2026, 9, 27, 9) if n == 0 else ist(2026, 9, 1 + n)) for n in range(14)]
    c, _ = setup(monkeypatch, many)
    recent = dash(c, "year")["recent"]
    assert len(recent) == 10
    assert recent[0]["created_by_name"] == "Ravi Kumar"
    assert recent[0]["created_at"] > recent[-1]["created_at"]


def test_monthly_buckets_cover_fy_months_to_date(monkeypatch):
    c, _ = setup(monkeypatch, QUOTES)
    months = dash(c, "year")["monthly"]
    assert [m["label"] for m in months] == ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    assert [m["quotations"] for m in months] == [1, 0, 0, 1, 0, 3]
    assert dash(c, "30d")["monthly"] == []


def test_empty_period(monkeypatch):
    c, _ = setup(monkeypatch, [])
    d = dash(c, "today")
    assert d["totals"] == {"quotations": 0, "value": 0, "average": 0}
    assert d["by_person"] == [] and d["recent"] == [] and d["top_customers"] == []


def test_labels_name_the_financial_year(monkeypatch):
    c, _ = setup(monkeypatch, [])
    assert dash(c, "year")["label"] == "FY 26-27 (1 Apr 2026 – 27 Sep 2026)"
    assert dash(c, "quarter")["label"] == "Q2 FY 26-27 (1 Jul 2026 – 27 Sep 2026)"


def test_dashboard_is_admin_only():
    c, _ = make_client(role="user")
    assert c.get("/api/v1/dashboard?period=today").status_code == 403


def test_unknown_period_rejected():
    c, _ = make_client(role="admin")
    assert c.get("/api/v1/dashboard?period=decade").status_code == 422


def test_quote_list_shows_creator_name(monkeypatch):
    c, db = setup(monkeypatch, QUOTES[:1])
    assert c.get("/api/v1/quotes").json()[0]["created_by_name"] == "Ravi Kumar"
