from decimal import ROUND_HALF_UP, Decimal

from app.schemas.quote import QuoteItemIn

PAISA = Decimal("0.01")


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(PAISA, rounding=ROUND_HALF_UP)


def compute_totals(items: list[QuoteItemIn]) -> tuple[list[dict], Decimal]:
    """Row totals (None for label-only rows) and the quote subtotal, rounded half-up to paise."""
    rows, subtotal = [], Decimal("0")
    for it in items:
        row = it.model_dump()
        if it.priced:
            qty, price = _money(it.qty), _money(it.unit_price)
            row["qty"], row["unit_price"] = float(qty), float(price)
            total = (qty * price).quantize(PAISA, rounding=ROUND_HALF_UP)
            row["total"] = float(total)
            subtotal += total
        else:
            row["total"] = None
        rows.append(row)
    return rows, subtotal
