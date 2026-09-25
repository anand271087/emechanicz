import type { QuoteItemIn } from "../../lib/types";

/** Editable line-item row. qty/price are strings while typing. */
export interface Row {
  key: string;
  description: string;
  qty: string;
  unit_price: string;
  /** Shares one merged qty/price cell with the row above. */
  joinAbove: boolean;
}

let nextKey = 0;
export const newRow = (partial: Partial<Row> = {}): Row => ({
  key: `r${nextKey++}`, description: "", qty: "", unit_price: "", joinAbove: false, ...partial,
});

const num = (s: string) => (s.trim() === "" ? null : Number(s));

function groupIds(rows: Row[]): (number | null)[] {
  const ids: (number | null)[] = rows.map(() => null);
  let next = 1;
  rows.forEach((r, i) => {
    if (!r.joinAbove || i === 0) return;
    if (ids[i - 1] === null) ids[i - 1] = next++;
    ids[i] = ids[i - 1];
  });
  return ids;
}

export function toApiItems(rows: Row[]): QuoteItemIn[] {
  const ids = groupIds(rows);
  return rows.map((r, i) => ({
    sl_no: i + 1,
    description: r.description.trim(),
    qty: num(r.qty),
    unit_price: num(r.unit_price),
    group_id: ids[i],
  }));
}

export function fromApiItems(items: QuoteItemIn[]): Row[] {
  const sorted = [...items].sort((a, b) => a.sl_no - b.sl_no);
  return sorted.map((it, i) =>
    newRow({
      description: it.description,
      qty: it.qty === null ? "" : String(it.qty),
      unit_price: it.unit_price === null ? "" : String(it.unit_price),
      joinAbove: i > 0 && it.group_id !== null && it.group_id === sorted[i - 1].group_id,
    }),
  );
}

export function rowTotal(r: Row): number | null {
  const q = num(r.qty);
  const p = num(r.unit_price);
  return q === null || p === null || Number.isNaN(q) || Number.isNaN(p) ? null : q * p;
}

export function subtotal(rows: Row[]): number {
  const paise = rows.reduce((sum, r) => sum + Math.round((rowTotal(r) ?? 0) * 100), 0);
  return paise / 100;
}

export function validateRows(rows: Row[]): string[] {
  const errors: string[] = [];
  rows.forEach((r, i) => {
    const n = i + 1;
    if (!r.description.trim()) errors.push(`Row ${n}: add a description`);
    const q = num(r.qty);
    const p = num(r.unit_price);
    if ((q === null) !== (p === null)) {
      errors.push(`Row ${n}: enter both qty and price, or leave both blank`);
    } else if (q !== null && p !== null && (!(q >= 0) || !(p >= 0))) {
      errors.push(`Row ${n}: qty and price must be positive numbers`);
    }
    if (i === 0 && r.joinAbove) errors.push("Row 1 has no row above to share a price with");
  });
  const ids = groupIds(rows);
  const seen = new Set<number>();
  ids.forEach((g) => {
    if (g === null || seen.has(g)) return;
    seen.add(g);
    const members = ids.flatMap((x, i) => (x === g ? [i] : []));
    const priced = members.filter((i) => num(rows[i].qty) !== null);
    if (priced.length > 1) {
      errors.push(`Rows ${members[0] + 1}–${members[members.length - 1] + 1} share one price: ` +
        "enter qty and price on only one of them");
    }
  });
  return errors;
}
