import pytest
from pydantic import ValidationError

from app.schemas.quote import QuoteIn, QuoteItemIn
from app.services.quote_logic import compute_totals


def item(sl, desc="x", qty=None, price=None, group=None):
    return QuoteItemIn(sl_no=sl, description=desc, qty=qty, unit_price=price, group_id=group)


def test_totals_basic():
    rows, subtotal = compute_totals([item(1, "Rack", 2, 100.0)])
    assert rows[0]["total"] == 200.0 and subtotal == 200


def test_maxeye_quote_total():
    _, subtotal = compute_totals([item(1, "Pneumatic Fixture", 12, 137850.0)])
    assert subtotal == 1654200


def test_label_only_rows_ignored():
    rows, subtotal = compute_totals([item(1, "PC", 1, 500.0), item(2, "Documentation & Training")])
    assert rows[1]["total"] is None and subtotal == 500


def test_grouped_rows_price_counted_once():
    _, subtotal = compute_totals([item(1, "Installation", group=1),
                                  item(2, "Training", 1, 40000.0, group=1)])
    assert subtotal == 40000


def test_paise_preserved():
    _, subtotal = compute_totals([item(1, "A", 3, 33.33)])
    assert str(subtotal) == "99.99"


def base_quote(items):
    return dict(ref_no="ETS/P302/26-27", customer_id="c1", quote_date="2026-09-25", items=items)


def test_group_with_two_priced_rows_rejected():
    with pytest.raises(ValidationError, match="one priced row"):
        QuoteIn(**base_quote([dict(sl_no=1, description="a", qty=1, unit_price=5, group_id=1),
                              dict(sl_no=2, description="b", qty=1, unit_price=5, group_id=1)]))


def test_non_contiguous_group_rejected():
    with pytest.raises(ValidationError, match="consecutive"):
        QuoteIn(**base_quote([dict(sl_no=1, description="a", group_id=1),
                              dict(sl_no=2, description="b", qty=1, unit_price=5),
                              dict(sl_no=3, description="c", qty=1, unit_price=5, group_id=1)]))


def test_negative_price_rejected():
    with pytest.raises(ValidationError):
        QuoteIn(**base_quote([dict(sl_no=1, description="a", qty=1, unit_price=-5)]))


def test_qty_without_price_rejected():
    with pytest.raises(ValidationError, match="both"):
        QuoteIn(**base_quote([dict(sl_no=1, description="a", qty=1)]))


def test_blank_ref_rejected():
    with pytest.raises(ValidationError):
        QuoteIn(**{**base_quote([]), "ref_no": "  "})
