export interface Part {
  text: string;
  match: boolean;
}

const normalise = (s: string) => s.toLowerCase().split(/\s+/).filter(Boolean).join(" ");

export const sameDescription = (a: string, b: string) => normalise(a) === normalise(b);

/** Split text around the first case-insensitive occurrence of query, for highlighting. */
export function matchParts(text: string, query: string): Part[] {
  const q = normalise(query);
  const at = q ? text.toLowerCase().indexOf(q) : -1;
  if (at < 0) return [{ text, match: false }];
  return [
    { text: text.slice(0, at), match: false },
    { text: text.slice(at, at + q.length), match: true },
    { text: text.slice(at + q.length), match: false },
  ].filter((p) => p.text);
}
