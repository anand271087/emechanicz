from datetime import date


def financial_year(d: date) -> str:
    """Indian financial year (April–March) as 'YY-YY', e.g. '26-27'."""
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start % 100:02d}-{(start + 1) % 100:02d}"


def format_ref(prefix: str, seq: int, fy: str) -> str:
    return f"ETS/{prefix}{seq}/{fy}"


def next_ref_state(state: dict, today: date) -> tuple[str, dict]:
    """Next ref number from the stored sequence; restarts at 1 in a new FY."""
    fy = financial_year(today)
    seq = state["seq"] + 1 if state.get("fy") == fy else 1
    new_state = {"prefix": state.get("prefix", "P"), "fy": fy, "seq": seq}
    return format_ref(new_state["prefix"], seq, fy), new_state
