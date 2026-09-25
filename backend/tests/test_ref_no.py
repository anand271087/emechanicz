from datetime import date

from app.services.ref_no import financial_year, next_ref_state


def test_fy_april_onward():
    assert financial_year(date(2026, 9, 1)) == "26-27"


def test_fy_jan_to_march_belongs_to_previous_year():
    assert financial_year(date(2027, 3, 31)) == "26-27"


def test_fy_rolls_on_april_first():
    assert financial_year(date(2027, 4, 1)) == "27-28"


def test_next_ref_increments():
    ref, state = next_ref_state({"prefix": "P", "fy": "26-27", "seq": 301}, date(2026, 9, 25))
    assert ref == "ETS/P302/26-27"
    assert state["seq"] == 302


def test_next_ref_fy_rollover_resets_sequence():
    ref, state = next_ref_state({"prefix": "P", "fy": "26-27", "seq": 301}, date(2027, 4, 1))
    assert ref == "ETS/P1/27-28"
    assert state == {"prefix": "P", "fy": "27-28", "seq": 1}
