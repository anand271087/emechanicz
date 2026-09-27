import { useEffect, useState } from "react";
import { Button, EmptyState, ErrorNote, Field, Input, Modal, PageHeader, Spinner, useToast } from "../../components/ui";
import { api, del, put } from "../../lib/api";
import type { ItemDescription } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";

export default function Items() {
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<ItemDescription | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setQuery(search), 250);
    return () => clearTimeout(t);
  }, [search]);

  const { data, error, loading, reload } = useLoad(
    () => api<ItemDescription[]>(`/api/v1/item-descriptions?q=${encodeURIComponent(query)}&limit=200`),
    [query],
  );

  async function remove(item: ItemDescription) {
    if (!confirm(`Remove "${item.description}" from the suggestions? Quotations that use it are not changed.`)) return;
    try {
      await del(`/api/v1/item-descriptions/${item.id}`);
      toast("Removed from suggestions");
      reload();
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }

  return (
    <>
      <PageHeader title="Items">
        <p className="text-muted">Descriptions suggested in the quotation builder. New ones are added when a quotation is saved.</p>
      </PageHeader>
      <Input type="search" placeholder="Search items" value={search} onChange={(e) => setSearch(e.target.value)}
        className="mb-4 sm:max-w-sm" aria-label="Search items" />

      {error && <ErrorNote message={error} />}
      {loading && !data ? <Spinner /> : !data?.length ? (
        query ? <EmptyState title="No matching items" body="Check the spelling, or type the new description in a quotation." />
          : <EmptyState title="No saved items yet" body="Descriptions you type in quotations appear here after you save the quotation." />
      ) : (
        <ul className="divide-y divide-line overflow-hidden rounded-lg border border-line bg-white">
          {data.map((item) => (
            <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
              <span className="min-w-0 flex-1 whitespace-pre-line">{item.description}</span>
              <span className="flex gap-4 text-sm font-medium">
                <button onClick={() => setEditing(item)} className="text-navy hover:underline">Edit</button>
                <button onClick={() => remove(item)} className="text-danger hover:underline">Remove</button>
              </span>
            </li>
          ))}
        </ul>
      )}

      <Modal open={editing !== null} onClose={() => setEditing(null)} title="Edit item">
        {editing && <EditForm key={editing.id} item={editing} onCancel={() => setEditing(null)}
          onSaved={() => { toast("Item saved"); setEditing(null); reload(); }} />}
      </Modal>
    </>
  );
}

function EditForm({ item, onSaved, onCancel }: { item: ItemDescription; onSaved: () => void; onCancel: () => void }) {
  const [text, setText] = useState(item.description);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    setError("");
    try {
      await put(`/api/v1/item-descriptions/${item.id}`, { description: text });
      onSaved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); save(); }} className="space-y-3">
      <Field label="Description" hint="Changing it here only affects future suggestions, not saved quotations.">
        {(id) => <Input id={id} required value={text} onChange={(e) => setText(e.target.value)} autoFocus />}
      </Field>
      {error && <ErrorNote message={error} />}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" busy={busy}>Save item</Button>
      </div>
    </form>
  );
}
