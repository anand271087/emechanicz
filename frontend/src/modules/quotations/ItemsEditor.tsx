import { Button, Input, Textarea } from "../../components/ui";
import { formatINR } from "../../lib/inr";
import { newRow, rowTotal, subtotal, type Row } from "./itemsLogic";

interface Props {
  rows: Row[];
  onChange: (rows: Row[]) => void;
  words: string;
}

export default function ItemsEditor({ rows, onChange, words }: Props) {
  const update = (i: number, patch: Partial<Row>) =>
    onChange(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const remove = (i: number) => {
    const next = rows.filter((_, j) => j !== i);
    if (next[0]) next[0] = { ...next[0], joinAbove: false };
    onChange(next);
  };
  const move = (i: number, dir: -1 | 1) => {
    const j = i + dir;
    if (j < 0 || j >= rows.length) return;
    const next = [...rows];
    [next[i], next[j]] = [next[j], next[i]];
    next[0] = { ...next[0], joinAbove: false };
    onChange(next);
  };

  return (
    <div>
      <div className="hidden grid-cols-[2.5rem_1fr_5rem_8rem_8rem_5.5rem] gap-2 border-b border-line bg-fixture
        px-3 py-2 text-sm font-semibold text-navy md:grid">
        <span className="text-center">Sl.No.</span><span>Description</span><span className="text-center">Qty</span>
        <span className="text-right">Unit price</span><span className="text-right">Total</span><span />
      </div>

      <ol className="divide-y divide-line">
        {rows.map((r, i) => {
          const total = rowTotal(r);
          return (
            <li key={r.key} className={`grid grid-cols-[2rem_1fr] gap-x-2 gap-y-2 px-3 py-3
              md:grid-cols-[2.5rem_1fr_5rem_8rem_8rem_5.5rem] md:items-start
              ${r.joinAbove ? "bg-fixture-soft/60" : ""}`}>
              <span className="pt-2 text-center font-semibold text-navy">{i + 1}</span>

              <div className="min-w-0">
                <Textarea aria-label={`Row ${i + 1} description`} rows={1} value={r.description}
                  placeholder="Item description"
                  onChange={(e) => update(i, { description: e.target.value })}
                  className="field-sizing-content min-h-10 resize-none" />
                {i > 0 && (
                  <label className="mt-1.5 inline-flex items-center gap-2 text-sm text-muted">
                    <input type="checkbox" checked={r.joinAbove} className="size-4 accent-navy"
                      onChange={(e) => update(i, { joinAbove: e.target.checked })} />
                    Share one price with the row above
                  </label>
                )}
              </div>

              <div className="col-start-2 grid grid-cols-3 gap-2 md:contents">
                <label className="md:block">
                  <span className="mb-0.5 block text-xs text-muted md:sr-only">Qty</span>
                  <Input inputMode="decimal" aria-label={`Row ${i + 1} qty`} value={r.qty}
                    onChange={(e) => update(i, { qty: e.target.value })} className="text-center" />
                </label>
                <label className="md:block">
                  <span className="mb-0.5 block text-xs text-muted md:sr-only">Unit price</span>
                  <Input inputMode="decimal" aria-label={`Row ${i + 1} unit price`} value={r.unit_price}
                    onChange={(e) => update(i, { unit_price: e.target.value })} className="text-right" />
                </label>
                <div>
                  <span className="mb-0.5 block text-xs text-muted md:sr-only">Total</span>
                  <p className="py-2 text-right font-semibold">{total === null ? "—" : formatINR(total)}</p>
                </div>
              </div>

              <div className="col-start-2 flex justify-end gap-1 md:col-start-auto md:pt-1">
                <IconBtn label={`Move row ${i + 1} up`} onClick={() => move(i, -1)} disabled={i === 0}>↑</IconBtn>
                <IconBtn label={`Move row ${i + 1} down`} onClick={() => move(i, 1)}
                  disabled={i === rows.length - 1}>↓</IconBtn>
                <IconBtn label={`Remove row ${i + 1}`} onClick={() => remove(i)} danger>✕</IconBtn>
              </div>
            </li>
          );
        })}
      </ol>

      <div className="flex flex-col gap-3 border-t border-line px-3 py-3 sm:flex-row sm:items-start sm:justify-between">
        <Button variant="secondary" onClick={() => onChange([...rows, newRow()])}>Add row</Button>
        <div className="text-right">
          <p className="text-sm text-muted">Grand total (INR)</p>
          <p className="text-2xl font-bold text-navy">{formatINR(subtotal(rows))}</p>
          <p className="text-sm text-muted">{words}</p>
        </div>
      </div>
    </div>
  );
}

function IconBtn({ label, danger, ...props }:
  React.ButtonHTMLAttributes<HTMLButtonElement> & { label: string; danger?: boolean }) {
  return (
    <button type="button" aria-label={label} title={label} {...props}
      className={`grid size-9 place-items-center rounded-md border border-line bg-white text-sm
        disabled:opacity-30 ${danger ? "text-danger hover:bg-danger-soft" : "text-navy hover:bg-fixture-soft"}`} />
  );
}
