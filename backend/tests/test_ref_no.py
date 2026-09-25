from datetime import date

from app.services.ref_no import financial_year, format_ref, parse_seq


def test_fy_april_onward():
    assert financial_year(date(2026, 9, 1)) == "26-27"


def test_fy_jan_to_march_belongs_to_previous_year():
    assert financial_year(date(2027, 3, 31)) == "26-27"


def test_fy_rolls_on_april_first():
    assert financial_year(date(2027, 4, 1)) == "27-28"


def test_format_ref():
    assert format_ref("P", 302, "26-27") == "ETS/P302/26-27"


def test_parse_seq_matches_only_same_prefix_and_fy():
    assert parse_seq("ETS/P302/26-27", "P", "26-27") == 302
    assert parse_seq("ETS/SS10/26-27", "P", "26-27") is None
    assert parse_seq("ETS/P302/25-26", "P", "26-27") is None
