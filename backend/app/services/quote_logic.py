from decimal import Decimal

from app.schemas.quote import QuoteItemIn


def compute_totals(items: list[QuoteItemIn]) -> tuple[list[dict], Decimal]:
    """Row totals (None for label-only rows) and the quote subtotal."""
    rows, subtotal = [], Decimal("0")
    for it in items:
        row = it.model_dump()
        if it.priced:
            total = (Decimal(str(it.qty)) * Decimal(str(it.unit_price))).quantize(Decimal("0.01"))
            row["total"] = float(total)
            subtotal += total
        else:
            row["total"] = None
        rows.append(row)
    return rows, subtotal
