def table_rows(items: list[dict]) -> list[dict]:
    """Item rows ready to draw, with merged-price groups collapsed.

    Each row gets `span`: 1 for a normal row, N on the first row of an
    N-row merged group (carrying the group's qty/price/total), and 0 on the
    rows whose qty/price/total cells are covered by that merge.
    """
    rows = [dict(it, span=1) for it in sorted(items, key=lambda i: i["sl_no"])]
    i = 0
    while i < len(rows):
        g = rows[i].get("group_id")
        j = i + 1
        while g is not None and j < len(rows) and rows[j].get("group_id") == g:
            j += 1
        if j - i > 1:
            priced = next((r for r in rows[i:j] if r.get("qty") is not None), {})
            rows[i].update(span=j - i, qty=priced.get("qty"),
                           unit_price=priced.get("unit_price"), total=priced.get("total"))
            for r in rows[i + 1:j]:
                r["span"] = 0
        i = j
    return rows
