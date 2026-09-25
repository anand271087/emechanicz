import { useState } from "react";
import { Button, EmptyState, ErrorNote, Input, Modal, PageHeader, Spinner, useToast } from "../../components/ui";
import { api, del } from "../../lib/api";
import type { Customer } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";
import CustomerForm from "./CustomerForm";

export default function Customers() {
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Customer | "new" | null>(null);
  const { data, error, loading, reload } = useLoad(() => api<Customer[]>("/api/v1/customers"), []);

  const s = search.toLowerCase();
  const shown = (data ?? []).filter((c) =>
    !s || c.company_name.toLowerCase().includes(s) || c.contact_person.toLowerCase().includes(s));

  async function remove(c: Customer) {
    if (!confirm(`Delete ${c.company_name}? This can't be undone.`)) return;
    try {
      await del(`/api/v1/customers/${c.id}`);
      toast(`Deleted ${c.company_name}`);
      reload();
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }

  return (
    <>
      <PageHeader title="Customers" actions={<Button onClick={() => setEditing("new")}>Add customer</Button>} />
      <Input type="search" placeholder="Search customers" value={search} onChange={(e) => setSearch(e.target.value)}
        className="mb-4 sm:max-w-sm" aria-label="Search customers" />

      {error && <ErrorNote message={error} />}
      {loading && !data ? <Spinner /> : shown.length === 0 ? (
        search ? <EmptyState title="No matching customers" body="Check the spelling or add them as a new customer." />
          : <EmptyState title="No customers yet" body="Add a customer once and pick them for every quotation after that."
            action={<Button onClick={() => setEditing("new")}>Add customer</Button>} />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {shown.map((c) => (
            <li key={c.id} className="flex flex-col rounded-lg border border-line bg-white p-4">
              <p className="font-semibold text-navy">{c.company_name}</p>
              {c.contact_person && <p className="text-sm">{c.contact_person}</p>}
              <div className="mt-2 space-y-0.5 text-sm text-muted">
                {c.email && <p className="truncate"><a href={`mailto:${c.email}`} className="hover:text-navy">{c.email}</a></p>}
                {c.phone && <p><a href={`tel:${c.phone}`} className="hover:text-navy">{c.phone}</a></p>}
                {c.gst_no && <p>GST {c.gst_no}</p>}
              </div>
              <div className="mt-auto flex gap-4 pt-3 text-sm font-medium">
                <button onClick={() => setEditing(c)} className="text-navy hover:underline">Edit</button>
                <button onClick={() => remove(c)} className="text-danger hover:underline">Delete</button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Modal open={editing !== null} onClose={() => setEditing(null)}
        title={editing === "new" ? "Add customer" : "Edit customer"}>
        {editing !== null && (
          <CustomerForm key={editing === "new" ? "new" : editing.id}
            customer={editing === "new" ? undefined : editing}
            onCancel={() => setEditing(null)}
            onSaved={(c) => { toast(`Saved ${c.company_name}`); setEditing(null); reload(); }} />
        )}
      </Modal>
    </>
  );
}
