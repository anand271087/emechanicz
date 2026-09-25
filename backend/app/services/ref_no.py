import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def today_ist() -> date:
    return datetime.now(IST).date()


def financial_year(d: date) -> str:
    """Indian financial year (April–March) as 'YY-YY', e.g. '26-27'."""
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start % 100:02d}-{(start + 1) % 100:02d}"


def format_ref(prefix: str, seq: int, fy: str) -> str:
    return f"ETS/{prefix}{seq}/{fy}"


def parse_seq(ref_no: str, prefix: str, fy: str) -> int | None:
    """Sequence number of a ref in the ETS/<prefix><n>/<fy> pattern, else None."""
    m = re.fullmatch(rf"ETS/{re.escape(prefix)}(\d+)/{re.escape(fy)}", ref_no)
    return int(m.group(1)) if m else None
