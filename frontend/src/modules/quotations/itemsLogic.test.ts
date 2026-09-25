import { describe, expect, it } from "vitest";
import {
  financialYear, fromApiItems, rowTotal, subtotal, toApiItems, validateRows, type Row,
} from "./itemsLogic";

const row = (description: string, qty = "", unit_price = "", joinAbove = false): Row => ({
  key: description, description, qty, unit_price, joinAbove,
});

describe("toApiItems", () => {
  it("numbers rows and nulls blank qty/price", () => {
    expect(toApiItems([row("Rack", "1", "75200"), row("Training")])).toEqual([
      { sl_no: 1, description: "Rack", qty: 1, unit_price: 75200, group_id: null },
      { sl_no: 2, description: "Training", qty: null, unit_price: null, group_id: null },
    ]);
  });

  it("gives joined rows a shared group id", () => {
    const items = toApiItems([row("A"), row("Install"), row("Docs", "1", "40000", true), row("B", "1", "1")]);
    expect(items.map((i) => i.group_id)).toEqual([null, 1, 1, null]);
  });

  it("keeps separate groups distinct", () => {
    const items = toApiItems([row("A"), row("B", "", "", true), row("C"), row("D", "", "", true)]);
    expect(items.map((i) => i.group_id)).toEqual([1, 1, 2, 2]);
  });
});

describe("fromApiItems", () => {
  it("round-trips groups into joinAbove flags", () => {
    const rows = fromApiItems([
      { sl_no: 1, description: "A", qty: null, unit_price: null, group_id: 1 },
      { sl_no: 2, description: "B", qty: 1, unit_price: 5, group_id: 1 },
      { sl_no: 3, description: "C", qty: 1, unit_price: 5, group_id: null },
    ]);
    expect(rows.map((r) => r.joinAbove)).toEqual([false, true, false]);
    expect(rows[1].qty).toBe("1");
    expect(rows[0].qty).toBe("");
  });
});

describe("rowTotal", () => {
  it("rounds half-up to paise like the server", () => {
    expect(rowTotal(row("A", "2.5", "0.01"))).toBe(0.03);
    expect(rowTotal(row("A", "3", "0.1"))).toBe(0.3);
    expect(rowTotal(row("A", "12", "137850"))).toBe(1654200);
  });
});

describe("financialYear", () => {
  it("splits at April", () => {
    expect(financialYear("2027-03-31")).toBe("26-27");
    expect(financialYear("2027-04-01")).toBe("27-28");
  });
});

describe("subtotal", () => {
  it("sums only priced rows", () => {
    expect(subtotal([row("A", "12", "137850"), row("Label"), row("B", "2", "0.5")])).toBe(1654201);
  });
});

describe("validateRows", () => {
  it("accepts a valid quote", () => {
    expect(validateRows([row("A", "1", "5"), row("B")])).toEqual([]);
  });

  it("requires a description", () => {
    expect(validateRows([row("", "1", "5")])).toEqual(["Row 1: add a description"]);
  });

  it("requires qty and price together", () => {
    expect(validateRows([row("A", "1", "")])).toEqual(["Row 1: enter both qty and price, or leave both blank"]);
  });

  it("rejects negative or non-numeric values", () => {
    expect(validateRows([row("A", "-1", "5")])).toEqual(["Row 1: qty and price must be positive numbers"]);
    expect(validateRows([row("A", "x", "5")])).toEqual(["Row 1: qty and price must be positive numbers"]);
  });

  it("allows only one priced row per merged group", () => {
    expect(validateRows([row("A", "1", "5"), row("B", "1", "5", true)])).toEqual([
      "Rows 1–2 share one price: enter qty and price on only one of them",
    ]);
  });

  it("does not allow the first row to join above", () => {
    expect(validateRows([row("A", "", "", true)])).toEqual(["Row 1 has no row above to share a price with"]);
  });
});
