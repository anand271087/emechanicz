import re
from datetime import date


def inr(value) -> str:
    """Indian digit grouping with 2 decimals: 2138000 -> '21,38,000.00'."""
    if value is None:
        return ""
    whole, dec = f"{float(value):.2f}".split(".")
    sign = "-" if whole.startswith("-") else ""
    digits = whole.lstrip("-")
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return f"{sign}{digits}.{dec}"


def qty(value) -> str:
    if value is None:
        return ""
    return f"{float(value):g}"


def format_date(value) -> str:
    d = value if isinstance(value, date) else date.fromisoformat(str(value)[:10])
    return d.strftime("%d-%m-%Y")


ORDINAL_RE = re.compile(r"\b(\d+)(st|nd|rd|th)\b")


def download_name(quote: dict, ext: str) -> str:
    company = (quote.get("customers") or {}).get("company_name", "")
    raw = f"Quote-{quote['ref_no'].replace('/', '-')}-{company}".strip("-")
    return re.sub(r"[^A-Za-z0-9 ._-]", "", raw).strip() + f".{ext}"
