import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { Button, EmptyState, ErrorNote, Field, Input, Modal, PageHeader, Spinner, useToast } from "../../components/ui";
import { api, del, post, put, uploadFile } from "../../lib/api";
import type { ItemDescription, ItemImportResult } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

export function importSummary(r: ItemImportResult): string {
  const skipped = [
    r.already_in_list && `${plural(r.already_in_list, "item")} already in the list`,
    r.repeated_in_file && `${plural(r.repeated_in_file, "repeat")} in the file`,
    r.blank_rows && plural(r.blank_rows, "blank row"),
  ].filter(Boolean);
  return `Added ${plural(r.added, "item")}.` + (skipped.length ? ` Skipped ${skipped.join(", ")}.` : "");
}

export default function Items() {
  const toast = useToast();
  const fileInput = useRef<HTMLInputElement>(null);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<ItemDescription | "new" | null>(null);
  const [uploading, setUploading] = useState(false);
  const [summary, setSummary] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setQuery(search), 250);
    return () => clearTimeout(t);
  }, [search]);

  const { data, error, loading, reload } = useLoad(
    () => api<ItemDescription[]>(`/api/v1/item-descriptions?q=${encodeURIComponent(query)}&limit=1000&sort=name`),
    [query],
  );

  async function upload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setUploading(true);
    setSummary("");
    try {
      const result = await uploadFile<ItemImportResult>("/api/v1/item-descriptions/import", file);
      setSummary(importSummary(result));
      reload();
    } catch (err) {
      toast((err as Error).message, "error");
    } finally {
      setUploading(false);
    }
  }

  async function remove(item: ItemDescription) {
    if (!confirm(`Remove "${item.description}" from the suggestions? Quotations that use it are not changed.`)) return;
    try {
      await del(`/api/v1/item-descriptions/${item.id}`);
      toast("Removed from suggestions");
      reload();
    } catch (err) {
      toast((err as Error).message, "error");
    }
  }

  return (
    <>
      <PageHeader title="Items"
        actions={<>
          <a href="/items-template.xlsx" download="items-template.xlsx"
            className="inline-flex min-h-10 items-center rounded-md px-4 text-[15px] font-semibold text-navy hover:bg-fixture-soft">
            Download template
          </a>
          <Button variant="secondary" busy={uploading} onClick={() => fileInput.current?.click()}>Upload Excel</Button>
          <Button onClick={() => setEditing("new")}>Add item</Button>
          <input ref={fileInput} type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            className="hidden" onChange={upload} aria-label="Excel file to upload" />
        </>}>
        <p className="text-muted">Descriptions suggested in the quotation builder. New ones are added when a quotation is saved.</p>
      </PageHeader>

      {summary && (
        <div role="status" className="mb-4 flex items-start justify-between gap-3 rounded-md bg-sent-soft px-4 py-3 text-sent">
          <span>{summary}</span>
          <button onClick={() => setSummary("")} aria-label="Dismiss" className="font-semibold">✕</button>
        </div>
      )}

      <Input type="search" placeholder="Search items" value={search} onChange={(e) => setSearch(e.target.value)}
        className="mb-4 sm:max-w-sm" aria-label="Search items" />

      {error && <ErrorNote message={error} />}
      {loading && !data ? <Spinner /> : !data?.length ? (
        query ? <EmptyState title="No matching items" body="Check the spelling, or add it with Add item." />
          : <EmptyState title="No saved items yet"
            body="Add items one by one, upload an Excel list, or just save a quotation. Its descriptions are added here."
            action={<Button onClick={() => setEditing("new")}>Add item</Button>} />
      ) : (
        <>
          <p className="mb-2 text-sm text-muted">{plural(data.length, "item")}{data.length === 1000 ? " shown. Search to narrow the list" : ""}</p>
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
        </>
      )}

      <Modal open={editing !== null} onClose={() => setEditing(null)} title={editing === "new" ? "Add item" : "Edit item"}>
        {editing && <ItemForm key={editing === "new" ? "new" : editing.id} item={editing === "new" ? undefined : editing}
          onCancel={() => setEditing(null)}
          onSaved={(saved) => { toast(`Saved "${saved.description}"`); setEditing(null); reload(); }} />}
      </Modal>
    </>
  );
}

function ItemForm({ item, onSaved, onCancel }:
  { item?: ItemDescription; onSaved: (saved: ItemDescription) => void; onCancel: () => void }) {
  const [text, setText] = useState(item?.description ?? "");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    setError("");
    try {
      const saved = item
        ? await put<ItemDescription>(`/api/v1/item-descriptions/${item.id}`, { description: text })
        : await post<ItemDescription>("/api/v1/item-descriptions", { description: text });
      onSaved(saved);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); save(); }} className="space-y-3">
      <Field label="Description" hint={item
        ? "Changing it here only affects future suggestions, not saved quotations."
        : "The first letter is capitalised automatically."}>
        {(id) => <Input id={id} required value={text} onChange={(e) => setText(e.target.value)} autoFocus />}
      </Field>
      {error && <ErrorNote message={error} />}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" busy={busy}>{item ? "Save item" : "Add item"}</Button>
      </div>
    </form>
  );
}
