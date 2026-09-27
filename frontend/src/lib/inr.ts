export function formatINR(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  const [whole, dec] = Math.abs(value).toFixed(2).split(".");
  const tail = whole.slice(-3);
  let head = whole.slice(0, -3);
  const groups: string[] = [];
  while (head.length > 2) {
    groups.unshift(head.slice(-2));
    head = head.slice(0, -2);
  }
  if (head) groups.unshift(head);
  const grouped = [...groups, tail].join(",");
  return `${value < 0 ? "-" : ""}${grouped}.${dec}`;
}

export function formatDate(iso: string): string {
  const [y, m, d] = iso.slice(0, 10).split("-");
  return `${d}-${m}-${y}`;
}

/** Short rupee amount for headline numbers: ₹17.14 L, ₹2.35 Cr, ₹60 K. */
export function compactINR(value: number): string {
  const units: [number, string][] = [[1e7, "Cr"], [1e5, "L"], [1e3, "K"]];
  for (const [size, unit] of units) {
    if (Math.abs(value) >= size) return `₹${Number((value / size).toFixed(2))} ${unit}`;
  }
  return `₹${Math.round(value)}`;
}
