import { Button, Textarea } from "../../components/ui";

export default function TermsEditor({ terms, onChange, onReset }:
  { terms: string[]; onChange: (t: string[]) => void; onReset: () => void }) {
  const set = (i: number, v: string) => onChange(terms.map((t, j) => (j === i ? v : t)));
  return (
    <div className="space-y-2">
      <p className="text-sm text-muted">Extra lines inside a term print in bold, like the order address.</p>
      <ol className="space-y-2">
        {terms.map((t, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className="w-6 pt-2 text-right font-semibold text-navy">{i + 1}</span>
            <Textarea aria-label={`Term ${i + 1}`} rows={1} value={t} onChange={(e) => set(i, e.target.value)}
              className="field-sizing-content min-h-10 flex-1 resize-none" />
            <button type="button" aria-label={`Remove term ${i + 1}`} title="Remove term"
              onClick={() => onChange(terms.filter((_, j) => j !== i))}
              className="grid size-10 shrink-0 place-items-center rounded-md border border-line text-danger hover:bg-danger-soft">
              ✕
            </button>
          </li>
        ))}
      </ol>
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="secondary" onClick={() => onChange([...terms, ""])}>Add term</Button>
        <Button type="button" variant="ghost" onClick={onReset}>Reset to default terms</Button>
      </div>
    </div>
  );
}
