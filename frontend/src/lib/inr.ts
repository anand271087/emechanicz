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
